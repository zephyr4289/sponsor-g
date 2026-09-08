"""
Joins the sponsor register to Companies House, and derives risk signals.

Why this exists, and why it is the most valuable thing in the repo:

The sponsor register says an employer *may* sponsor a visa. It says nothing
about whether that employer is a going concern. Companies House says whether
the company is in liquidation, whether it files as dormant, whether its
accounts are overdue, and what it actually does for a living.

Neither source is interesting alone. Joined, they answer a question nobody
else answers: **is the employer about to sponsor my visa actually trading?**
A company in liquidation can sit on the register for months, because the
register is a licence list and not a health check. Someone accepting a job
there is betting their immigration status on a shell.

The join is also the moat. The two datasets are both free, but matching a
sponsor name to a company record is real work, and a competitor does not get
it for free by downloading the same files.

Two things it deliberately does not do:

- It does not guess. An unmatched sponsor stays unmatched rather than being
  attached to a similarly named company. A wrong match here would tell
  someone their prospective employer is in liquidation when it is not.
- It does not give advice. It reports what Companies House records and links
  to the source, and the caller is responsible for saying so.

Pure functions only, so all of it is testable without a network. The download
and streaming live in enrich.py.
"""

import re
from datetime import date, datetime

# Companies House column names, after stripping the stray spaces its own
# header contains (" CompanyNumber" really is spelled with a leading space).
COL_NAME = "CompanyName"
COL_NUMBER = "CompanyNumber"
COL_STATUS = "CompanyStatus"
COL_CATEGORY = "CompanyCategory"
COL_INCORPORATED = "IncorporationDate"
COL_ACCOUNTS_DUE = "Accounts.NextDueDate"
COL_ACCOUNTS_CATEGORY = "Accounts.AccountCategory"
COL_CONFSTMT_DUE = "ConfStmtNextDueDate"
COL_MORTGAGES = "Mortgages.NumMortOutstanding"
COL_POSTTOWN = "RegAddress.PostTown"
SIC_COLUMNS = [f"SICCode.SicText_{n}" for n in (1, 2, 3, 4)]
PREVIOUS_NAME_COLUMNS = [f"PreviousName_{n}.CompanyName" for n in range(1, 11)]

# A company incorporated more recently than this, already holding a licence to
# sponsor visas, is unusual enough to be worth showing. Not wrong, just young.
NEW_COMPANY_DAYS = 365

# Legal suffixes are normalised rather than removed. Removing them collapses
# genuinely different companies ("Foo Ltd" and "Foo LLP") onto one key.
SUFFIX_ALIASES = [
    (r"\bLIMITED\b", "LTD"),
    (r"\bPUBLIC LIMITED COMPANY\b", "PLC"),
    (r"\bCOMPANY\b", "CO"),
    (r"\bINCORPORATED\b", "INC"),
]

# The register writes trading names into the legal name. Companies House does
# not, so the part before the marker is what can match.
TRADING_AS = re.compile(
    r"\s+(?:T/?A|TRADING AS|T/AS)\b.*$", re.I)


def strip_trading_as(name):
    """'Acme Ltd T/A Joe's Cafe' -> 'Acme Ltd'."""
    return TRADING_AS.sub("", str(name)).strip()


def normalise_name(name):
    """Reduce a company name to a key suitable for exact matching.

    Deliberately conservative. It removes punctuation and standardises legal
    suffixes and '&', and stops there. Anything cleverer risks matching two
    different companies, and a wrong match is worse here than no match.
    """
    text = strip_trading_as(name).upper()
    text = text.replace("&", " AND ")
    # Dots and apostrophes are deleted, not spaced, so "A.C.M.E." matches
    # "ACME" and "SMITH'S" matches "SMITHS". Spacing them instead would split
    # every dotted initialism into separate words and never match.
    text = re.sub(r"[.'’ʼ`]", "", text)
    text = re.sub(r"[^A-Z0-9 ]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    for pattern, replacement in SUFFIX_ALIASES:
        text = re.sub(pattern, replacement, text)
    text = re.sub(r"^THE ", "", text)
    return re.sub(r"\s+", " ", text).strip()


def build_index(sponsors, name_index=0):
    """Map normalised sponsor name -> list of positions in `sponsors`.

    A list, because two sponsors in different towns can share a name and both
    deserve the same company data.
    """
    index = {}
    for position, row in enumerate(sponsors):
        key = normalise_name(row[name_index])
        if key:
            index.setdefault(key, []).append(position)
    return index


def parse_uk_date(value):
    """Companies House writes dd/mm/yyyy. Returns None on anything else."""
    try:
        return datetime.strptime(str(value).strip(), "%d/%m/%Y").date()
    except (ValueError, TypeError):
        return None


def sic_industries(row):
    """The human-readable half of each SIC code, deduplicated in order."""
    out = []
    for column in SIC_COLUMNS:
        raw = (row.get(column) or "").strip()
        if not raw:
            continue
        # "62020 - Information technology consultancy activities"
        text = raw.split(" - ", 1)[1].strip() if " - " in raw else raw
        if text and text not in out:
            out.append(text)
    return out


def sic_codes(row):
    """Just the numeric codes, for anyone who wants to group by them."""
    out = []
    for column in SIC_COLUMNS:
        raw = (row.get(column) or "").strip()
        match = re.match(r"(\d{4,5})", raw)
        if match and match.group(1) not in out:
            out.append(match.group(1))
    return out


def risk_flags(row, today=None):
    """Signals worth telling someone about, each traceable to a field.

    These describe the company's filing record, not its character. The
    wording that reaches a reader must stay equally factual.
    """
    today = today or date.today()
    flags = []

    status = (row.get(COL_STATUS) or "").strip()
    if status and status.lower() != "active":
        flags.append("not_active")

    accounts_category = (row.get(COL_ACCOUNTS_CATEGORY) or "").strip().upper()
    if accounts_category == "DORMANT":
        flags.append("dormant")

    due = parse_uk_date(row.get(COL_ACCOUNTS_DUE))
    if due and due < today:
        flags.append("accounts_overdue")

    conf_due = parse_uk_date(row.get(COL_CONFSTMT_DUE))
    if conf_due and conf_due < today:
        flags.append("confirmation_statement_overdue")

    incorporated = parse_uk_date(row.get(COL_INCORPORATED))
    if incorporated and (today - incorporated).days < NEW_COMPANY_DAYS:
        flags.append("incorporated_recently")

    return flags


def company_record(row, today=None):
    """The subset of a Companies House row worth publishing."""
    incorporated = parse_uk_date(row.get(COL_INCORPORATED))
    return {
        "number": (row.get(COL_NUMBER) or "").strip(),
        "name": (row.get(COL_NAME) or "").strip(),
        "status": (row.get(COL_STATUS) or "").strip(),
        "category": (row.get(COL_CATEGORY) or "").strip(),
        "incorporated": incorporated.isoformat() if incorporated else "",
        "accounts": (row.get(COL_ACCOUNTS_CATEGORY) or "").strip(),
        "sic": sic_industries(row),
        "sic_codes": sic_codes(row),
        "town": (row.get(COL_POSTTOWN) or "").strip().title(),
        "flags": risk_flags(row, today),
    }


def match_keys(row):
    """Every name this company could be matched on: current and previous.

    Sponsors are slow to update, so a company that renamed still appears on
    the register under the old name. Matching previous names recovers those.
    """
    keys = []
    for column in [COL_NAME] + PREVIOUS_NAME_COLUMNS:
        value = (row.get(column) or "").strip()
        if not value:
            continue
        key = normalise_name(value)
        if key and key not in keys:
            keys.append(key)
    return keys


def join(rows, index, today=None):
    """Match Companies House rows against a sponsor index.

    `rows` is any iterable of dicts, so the caller can stream a 470MB
    download without holding it in memory. Returns
    {sponsor_position: company_record}.

    A sponsor already matched on its current name is never overwritten by a
    later match on somebody's previous name, which is the weaker signal.
    """
    matched = {}
    for row in rows:
        keys = match_keys(row)
        if not keys:
            continue
        record = None
        for rank, key in enumerate(keys):
            for position in index.get(key, ()):
                if position in matched and matched[position]["_rank"] <= rank:
                    continue
                if record is None:
                    record = company_record(row, today)
                matched[position] = dict(record, _rank=rank)
    for value in matched.values():
        value.pop("_rank", None)
    return matched
