"""Tests for the monthly Companies House enrichment job.

Run from the repo root:
    python -m unittest discover -s pipeline -v
"""

import io
import unittest
import zipfile
from datetime import date

import companies as ch
import enrich


HEADER = [
    "CompanyName", " CompanyNumber", "RegAddress.PostTown", "CompanyCategory",
    "CompanyStatus", "IncorporationDate", "Accounts.NextDueDate",
    "Accounts.AccountCategory", "SICCode.SicText_1", "ConfStmtNextDueDate",
    "PreviousName_1.CompanyName",
]
TODAY = date(2026, 9, 8)


def make_zip(rows):
    """A Companies House style zip, complete with its stray header spaces."""
    body = ",".join(HEADER) + "\n"
    for r in rows:
        body += ",".join('"%s"' % str(r.get(h.strip(), "")) for h in HEADER) + "\n"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("BasicCompanyData-2026-09-01-part1_7.csv", body)
    buf.seek(0)
    return buf


def ch_row(name, **kw):
    row = {
        "CompanyName": name, "CompanyNumber": "01234567",
        "CompanyStatus": "Active", "CompanyCategory": "Private Limited Company",
        "IncorporationDate": "11/09/2012", "Accounts.NextDueDate": "30/06/2027",
        "Accounts.AccountCategory": "MICRO ENTITY",
        "ConfStmtNextDueDate": "30/06/2027",
        "SICCode.SicText_1": "87300 - Residential care",
        "RegAddress.PostTown": "LEEDS",
    }
    row.update(kw)
    return row


def sponsor(name, town="Leeds"):
    return [name, town, "", "Other", ["Skilled Worker"], "A"]


class SnapshotNameTests(unittest.TestCase):

    def test_uses_the_first_of_the_month(self):
        self.assertEqual(enrich.snapshot_name(date(2026, 9, 8)), "2026-09-01")

    def test_pads_single_digit_months(self):
        self.assertEqual(enrich.snapshot_name(date(2026, 1, 31)), "2026-01-01")

    def test_builds_all_seven_part_urls(self):
        urls = enrich.part_urls("2026-09-01")
        self.assertEqual(len(urls), 7)
        self.assertTrue(urls[0].endswith("part1_7.zip"))
        self.assertTrue(urls[-1].endswith("part7_7.zip"))


class ZipReadingTests(unittest.TestCase):

    def test_strips_the_stray_spaces_in_their_header(self):
        rows = list(enrich.rows_from_zip(make_zip([ch_row("ACME LTD")])))
        self.assertEqual(rows[0]["CompanyNumber"], "01234567")

    def test_reads_every_row(self):
        rows = list(enrich.rows_from_zip(
            make_zip([ch_row("A LTD"), ch_row("B LTD")])))
        self.assertEqual(len(rows), 2)

    def test_an_empty_csv_yields_nothing(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr("empty.csv", "")
        buf.seek(0)
        self.assertEqual(list(enrich.rows_from_zip(buf)), [])


class BuildTests(unittest.TestCase):

    def test_publishes_only_sponsors_carrying_a_signal(self):
        sponsors = [sponsor("Acme Care Ltd"), sponsor("Healthy Co Ltd")]
        rows = [ch_row("ACME CARE LIMITED", CompanyStatus="Liquidation"),
                ch_row("HEALTHY CO LTD")]
        published, stats = enrich.build(sponsors, rows, TODAY)
        self.assertEqual(list(published), [ch.normalise_name("Acme Care Ltd")])
        self.assertEqual(stats["matched"], 2)
        self.assertEqual(stats["flagged"], 1)

    def test_keys_on_the_normalised_name_not_the_row_position(self):
        # Positions shift daily as the register changes; this file is monthly.
        sponsors = [sponsor("Acme Care Ltd")]
        rows = [ch_row("ACME CARE LIMITED", CompanyStatus="Dissolved")]
        published, _ = enrich.build(sponsors, rows, TODAY)
        self.assertIn("ACME CARE LTD", published)

    def test_publishes_the_fields_the_site_needs(self):
        sponsors = [sponsor("Acme Care Ltd")]
        rows = [ch_row("ACME CARE LIMITED", CompanyStatus="Liquidation")]
        published, _ = enrich.build(sponsors, rows, TODAY)
        record = published["ACME CARE LTD"]
        self.assertEqual(record["status"], "Liquidation")
        self.assertEqual(record["number"], "01234567")
        self.assertIn("not_active", record["flags"])
        self.assertEqual(record["incorporated"], "2012-09-11")

    def test_counts_each_flag(self):
        sponsors = [sponsor("A Ltd"), sponsor("B Ltd")]
        rows = [ch_row("A LTD", CompanyStatus="Liquidation"),
                ch_row("B LTD", **{"Accounts.AccountCategory": "DORMANT"})]
        _, stats = enrich.build(sponsors, rows, TODAY)
        self.assertEqual(stats["flag_counts"]["not_active"], 1)
        self.assertEqual(stats["flag_counts"]["dormant"], 1)

    def test_match_rate_is_reported(self):
        sponsors = [sponsor("A Ltd"), sponsor("Nowhere Ltd")]
        _, stats = enrich.build(sponsors, [ch_row("A LTD")], TODAY)
        self.assertEqual(stats["match_rate"], 0.5)

    def test_no_sponsors_does_not_divide_by_zero(self):
        _, stats = enrich.build([], [ch_row("A LTD")], TODAY)
        self.assertEqual(stats["match_rate"], 0)

    def test_nothing_matched_publishes_nothing(self):
        published, stats = enrich.build([sponsor("Unrelated Ltd")],
                                        [ch_row("A LTD")], TODAY)
        self.assertEqual(published, {})
        self.assertEqual(stats["matched"], 0)

    def test_a_renamed_company_is_matched_on_its_previous_name(self):
        sponsors = [sponsor("Old Name Ltd")]
        rows = [ch_row("New Name Ltd", CompanyStatus="Liquidation",
                       **{"PreviousName_1.CompanyName": "OLD NAME LIMITED"})]
        published, _ = enrich.build(sponsors, rows, TODAY)
        self.assertIn(ch.normalise_name("Old Name Ltd"), published)


class GuardTests(unittest.TestCase):

    def test_the_floor_is_set_where_a_real_run_clears_it(self):
        # A real run matches about 88%; the floor exists to catch a schema or
        # download change, not to be tuned against normal variation.
        self.assertLess(enrich.MIN_MATCH_RATE, 0.88)
        self.assertGreater(enrich.MIN_MATCH_RATE, 0.4)


if __name__ == "__main__":
    unittest.main()
