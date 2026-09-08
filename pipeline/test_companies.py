"""Tests for the Companies House join.

A wrong match here would tell someone their prospective employer is in
liquidation when it is not, so the tests lean hard on not matching rather
than on matching more.

Run from the repo root:
    python -m unittest discover -s pipeline -v
"""

import unittest
from datetime import date

import companies as ch


def ch_row(name="ACME CARE LTD", **kw):
    row = {
        ch.COL_NAME: name,
        ch.COL_NUMBER: "01234567",
        ch.COL_STATUS: "Active",
        ch.COL_CATEGORY: "Private Limited Company",
        ch.COL_INCORPORATED: "11/09/2012",
        ch.COL_ACCOUNTS_DUE: "30/06/2027",
        ch.COL_ACCOUNTS_CATEGORY: "MICRO ENTITY",
        ch.COL_CONFSTMT_DUE: "30/06/2027",
        ch.COL_POSTTOWN: "HARROGATE",
        "SICCode.SicText_1": "87300 - Residential care activities for the elderly",
    }
    row.update(kw)
    return row


TODAY = date(2026, 9, 8)


class NormaliseTests(unittest.TestCase):

    def test_limited_and_ltd_match(self):
        self.assertEqual(ch.normalise_name("Acme Care Limited"),
                         ch.normalise_name("ACME CARE LTD"))

    def test_punctuation_is_ignored(self):
        self.assertEqual(ch.normalise_name("A.C.M.E. Care, Ltd."),
                         ch.normalise_name("ACME Care Ltd"))

    def test_dotted_initialisms_match_their_plain_form(self):
        self.assertEqual(ch.normalise_name("J.D. Wetherspoon PLC"),
                         ch.normalise_name("JD Wetherspoon Plc"))

    def test_apostrophes_are_ignored(self):
        # The register also publishes these as a damaged byte sequence, so
        # the repaired and unrepaired spellings must both normalise the same.
        for variant in ["Sainsbury's Ltd", "Sainsburys Ltd",
                        "Sainsbury’s Ltd"]:
            self.assertEqual(ch.normalise_name(variant), "SAINSBURYS LTD",
                             variant)

    def test_ampersand_matches_the_word_and(self):
        self.assertEqual(ch.normalise_name("Smith & Sons Ltd"),
                         ch.normalise_name("Smith and Sons Ltd"))

    def test_leading_the_is_dropped(self):
        self.assertEqual(ch.normalise_name("The Beck Practice Ltd"),
                         ch.normalise_name("Beck Practice Ltd"))

    def test_trading_as_is_stripped(self):
        for variant in ["Acme Ltd T/A Joe's Cafe", "Acme Ltd TRADING AS Joes",
                        "Acme Ltd t/a Joes"]:
            self.assertEqual(ch.normalise_name(variant),
                             ch.normalise_name("Acme Ltd"), variant)

    def test_different_legal_forms_do_not_collapse(self):
        # Foo Ltd and Foo LLP are different companies.
        self.assertNotEqual(ch.normalise_name("Foo Ltd"),
                            ch.normalise_name("Foo LLP"))

    def test_different_names_do_not_collapse(self):
        self.assertNotEqual(ch.normalise_name("Acme Care Ltd"),
                            ch.normalise_name("Acme Homecare Ltd"))

    def test_empty_and_junk_names(self):
        self.assertEqual(ch.normalise_name(""), "")
        self.assertEqual(ch.normalise_name("!!!"), "")


class DateTests(unittest.TestCase):

    def test_parses_uk_order(self):
        self.assertEqual(ch.parse_uk_date("11/09/2012"), date(2012, 9, 11))

    def test_returns_none_on_junk(self):
        for junk in ["", "not a date", "2012-09-11", None]:
            self.assertIsNone(ch.parse_uk_date(junk), junk)


class SicTests(unittest.TestCase):

    def test_splits_code_from_description(self):
        row = ch_row(**{"SICCode.SicText_1": "62020 - IT consultancy activities"})
        self.assertEqual(ch.sic_industries(row), ["IT consultancy activities"])
        self.assertEqual(ch.sic_codes(row), ["62020"])

    def test_collects_all_four_and_dedupes(self):
        row = ch_row(**{
            "SICCode.SicText_1": "62020 - IT consultancy",
            "SICCode.SicText_2": "62090 - Other IT services",
            "SICCode.SicText_3": "62020 - IT consultancy",
            "SICCode.SicText_4": "",
        })
        self.assertEqual(ch.sic_industries(row),
                         ["IT consultancy", "Other IT services"])

    def test_handles_a_code_with_no_description(self):
        row = ch_row(**{"SICCode.SicText_1": "99999"})
        self.assertEqual(ch.sic_codes(row), ["99999"])


class RiskFlagTests(unittest.TestCase):

    def test_an_ordinary_active_company_has_no_flags(self):
        self.assertEqual(ch.risk_flags(ch_row(), TODAY), [])

    def test_flags_a_company_that_is_not_active(self):
        for status in ["Liquidation", "Dissolved", "In Administration"]:
            self.assertIn("not_active",
                          ch.risk_flags(ch_row(**{ch.COL_STATUS: status}), TODAY))

    def test_flags_a_dormant_filer(self):
        # A dormant company holding a licence to sponsor visas is the single
        # most useful thing this join surfaces.
        row = ch_row(**{ch.COL_ACCOUNTS_CATEGORY: "DORMANT"})
        self.assertIn("dormant", ch.risk_flags(row, TODAY))

    def test_flags_overdue_accounts(self):
        row = ch_row(**{ch.COL_ACCOUNTS_DUE: "01/01/2026"})
        self.assertIn("accounts_overdue", ch.risk_flags(row, TODAY))

    def test_does_not_flag_accounts_still_in_future(self):
        row = ch_row(**{ch.COL_ACCOUNTS_DUE: "01/01/2027"})
        self.assertNotIn("accounts_overdue", ch.risk_flags(row, TODAY))

    def test_flags_an_overdue_confirmation_statement(self):
        row = ch_row(**{ch.COL_CONFSTMT_DUE: "01/01/2026"})
        self.assertIn("confirmation_statement_overdue", ch.risk_flags(row, TODAY))

    def test_flags_a_recently_incorporated_company(self):
        row = ch_row(**{ch.COL_INCORPORATED: "01/06/2026"})
        self.assertIn("incorporated_recently", ch.risk_flags(row, TODAY))

    def test_does_not_flag_an_established_company(self):
        row = ch_row(**{ch.COL_INCORPORATED: "01/06/2015"})
        self.assertNotIn("incorporated_recently", ch.risk_flags(row, TODAY))

    def test_missing_dates_produce_no_flags_rather_than_crashing(self):
        row = ch_row(**{ch.COL_INCORPORATED: "", ch.COL_ACCOUNTS_DUE: "",
                        ch.COL_CONFSTMT_DUE: ""})
        self.assertEqual(ch.risk_flags(row, TODAY), [])


class IndexAndJoinTests(unittest.TestCase):

    def sponsors(self):
        return [
            ["Acme Care Limited", "Harrogate", "", "Healthcare & Care", ["Skilled Worker"], "A"],
            ["Beta Foods Ltd T/A Beta Grill", "Leeds", "", "Hospitality & Food", ["Skilled Worker"], "A"],
            ["Unmatched Widgets Ltd", "Hull", "", "Other", ["Skilled Worker"], "A"],
        ]

    def test_index_keys_on_the_normalised_name(self):
        index = ch.build_index(self.sponsors())
        self.assertIn(ch.normalise_name("ACME CARE LTD"), index)

    def test_index_groups_duplicate_names(self):
        rows = [["Acme Ltd", "Leeds"], ["Acme Ltd", "Hull"]]
        index = ch.build_index(rows)
        self.assertEqual(len(index[ch.normalise_name("Acme Ltd")]), 2)

    def test_matches_across_ltd_and_limited(self):
        index = ch.build_index(self.sponsors())
        matched = ch.join([ch_row("ACME CARE LTD")], index, TODAY)
        self.assertIn(0, matched)
        self.assertEqual(matched[0]["number"], "01234567")

    def test_matches_a_sponsor_whose_name_carries_a_trading_name(self):
        index = ch.build_index(self.sponsors())
        matched = ch.join([ch_row("BETA FOODS LIMITED")], index, TODAY)
        self.assertIn(1, matched)

    def test_leaves_an_unmatched_sponsor_alone(self):
        index = ch.build_index(self.sponsors())
        matched = ch.join([ch_row("ACME CARE LTD")], index, TODAY)
        self.assertNotIn(2, matched)

    def test_does_not_match_a_merely_similar_name(self):
        index = ch.build_index(self.sponsors())
        matched = ch.join([ch_row("ACME CARE SERVICES LTD")], index, TODAY)
        self.assertEqual(matched, {})

    def test_matches_on_a_previous_name(self):
        # The register lags renames, so the old name is still listed.
        index = ch.build_index(self.sponsors())
        row = ch_row("Renamed Holdings Ltd",
                     **{"PreviousName_1.CompanyName": "ACME CARE LIMITED"})
        matched = ch.join([row], index, TODAY)
        self.assertIn(0, matched)
        self.assertEqual(matched[0]["name"], "Renamed Holdings Ltd")

    def test_a_current_name_match_beats_a_previous_name_match(self):
        index = ch.build_index(self.sponsors())
        weak = ch_row("Someone Else Ltd",
                      **{"PreviousName_1.CompanyName": "ACME CARE LIMITED",
                         ch.COL_NUMBER: "99999999"})
        strong = ch_row("ACME CARE LTD", **{ch.COL_NUMBER: "01234567"})
        for order in ([weak, strong], [strong, weak]):
            matched = ch.join(order, index, TODAY)
            self.assertEqual(matched[0]["number"], "01234567",
                             "current name must win regardless of row order")

    def test_join_carries_the_flags_through(self):
        index = ch.build_index(self.sponsors())
        row = ch_row("ACME CARE LTD", **{ch.COL_STATUS: "Liquidation"})
        matched = ch.join([row], index, TODAY)
        self.assertIn("not_active", matched[0]["flags"])

    def test_internal_rank_is_not_published(self):
        index = ch.build_index(self.sponsors())
        matched = ch.join([ch_row("ACME CARE LTD")], index, TODAY)
        self.assertNotIn("_rank", matched[0])

    def test_an_empty_download_matches_nothing(self):
        self.assertEqual(ch.join([], ch.build_index(self.sponsors()), TODAY), {})


if __name__ == "__main__":
    unittest.main()
