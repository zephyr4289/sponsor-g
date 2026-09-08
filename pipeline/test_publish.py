"""Tests for the public/private boundary.

These are the tests that stop the moat being published by accident, so they
are deliberately blunt about naming the file that matters.

Run from the repo root:
    python -m unittest discover -s pipeline -v
"""

import re
import tempfile
import unittest
from pathlib import Path

import publish

ROOT = Path(__file__).resolve().parent.parent


class BoundaryTests(unittest.TestCase):

    def test_the_full_history_is_never_published(self):
        # If this ever fails, we are giving away the one thing a competitor
        # cannot download.
        self.assertIn("changes.json", publish.INTERNAL_DATA)
        self.assertNotIn("changes.json", publish.PUBLIC_DATA)

    def test_the_newsletter_body_is_never_published(self):
        self.assertIn("digest.md", publish.INTERNAL_DATA)

    def test_no_file_is_in_both_lists(self):
        overlap = set(publish.PUBLIC_DATA) & set(publish.INTERNAL_DATA)
        self.assertEqual(overlap, set())

    def test_every_entry_carries_a_reason(self):
        for table in (publish.PUBLIC_DATA, publish.INTERNAL_DATA):
            for name, why in table.items():
                self.assertTrue(why.strip(), f"{name} has no reason recorded")

    def test_warnings_stay_public_because_they_protect_people(self):
        self.assertIn("company_flags.json", publish.PUBLIC_DATA)


class SiteNeedsTests(unittest.TestCase):
    """The site must not be broken by the boundary."""

    def fetched_by_the_site(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        return set(re.findall(r"fetch\('data/([^']+)'\)", html))

    def test_everything_the_site_fetches_is_published(self):
        for name in self.fetched_by_the_site():
            self.assertIn(name, publish.PUBLIC_DATA,
                          f"the site fetches data/{name} but it is not public")

    def test_the_site_does_not_fetch_anything_internal(self):
        for name in self.fetched_by_the_site():
            self.assertNotIn(name, publish.INTERNAL_DATA)

    def test_the_site_actually_fetches_something(self):
        # Guards against the regex silently matching nothing and the two
        # tests above passing for the wrong reason.
        self.assertGreater(len(self.fetched_by_the_site()), 3)


class PlanTests(unittest.TestCase):

    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())

    def touch(self, *names):
        for n in names:
            (self.dir / n).write_text("{}", encoding="utf-8")

    def test_sorts_known_files_into_the_right_buckets(self):
        self.touch("sponsors.json", "changes.json", "meta.json")
        publish_, withhold, unknown = publish.plan(self.dir)
        self.assertEqual(publish_, ["meta.json", "sponsors.json"])
        self.assertEqual(withhold, ["changes.json"])
        self.assertEqual(unknown, [])

    def test_reports_a_file_nobody_classified(self):
        # The whole point: a new file must not default to either side.
        self.touch("something_new.json")
        _, _, unknown = publish.plan(self.dir)
        self.assertEqual(unknown, ["something_new.json"])

    def test_an_empty_data_directory_is_fine(self):
        self.assertEqual(publish.plan(self.dir), ([], [], []))


class PublicFileTests(unittest.TestCase):

    def test_finds_the_generated_landing_pages(self):
        found = publish.landing_dirs(ROOT)
        self.assertIn("london", found)
        self.assertNotIn("data", found)
        self.assertNotIn("pipeline", found)

    def test_never_offers_to_publish_the_private_folders(self):
        paths = publish.public_files(ROOT)
        for secret in ("pipeline", "outreach", ".github", ".claude"):
            self.assertFalse(any(p == secret or p.startswith(secret + "/")
                                 for p in paths),
                             f"{secret} must never be published")

    def test_never_offers_to_publish_the_history(self):
        self.assertNotIn("data/changes.json", publish.public_files(ROOT))

    def test_includes_the_site_itself(self):
        paths = publish.public_files(ROOT)
        for needed in ("index.html", "sitemap.xml", "feed.xml", "changes",
                       "insights", "data-api"):
            self.assertIn(needed, paths)

    def test_describe_names_the_reason_for_the_history(self):
        self.assertIn("moat", publish.describe())


class LiveRepoTests(unittest.TestCase):

    def test_nothing_in_data_is_unclassified_right_now(self):
        _, _, unknown = publish.plan(ROOT / "data")
        self.assertEqual(unknown, [],
                         "classify these in pipeline/publish.py: "
                         + ", ".join(unknown))


if __name__ == "__main__":
    unittest.main()


class StageTests(unittest.TestCase):
    """stage() is what actually crosses the boundary, so it gets checked
    twice: once for what it copies, once by audit() on the result."""

    def setUp(self):
        self.dest = Path(tempfile.mkdtemp()) / "staged"

    def test_copies_the_site(self):
        staged = publish.stage(ROOT, self.dest)
        for needed in ("index.html", "sitemap.xml", "feed.xml",
                       "data/sponsors.json", "changes/index.html"):
            self.assertIn(needed, staged)
        self.assertTrue((self.dest / "index.html").exists())

    def test_never_stages_the_history(self):
        staged = publish.stage(ROOT, self.dest)
        self.assertNotIn("data/changes.json", staged)
        self.assertFalse((self.dest / "data" / "changes.json").exists())

    def test_never_stages_the_pipeline_or_private_notes(self):
        publish.stage(ROOT, self.dest)
        for secret in ("pipeline", "outreach", "internal", ".github", ".claude"):
            self.assertFalse((self.dest / secret).exists(),
                             f"{secret} was staged")

    def test_audit_passes_on_a_real_staging_run(self):
        self.assertEqual(publish.audit(publish.stage(ROOT, self.dest)), [])

    def test_audit_catches_the_history(self):
        self.assertEqual(publish.audit(["data/changes.json"]),
                         ["data/changes.json"])

    def test_audit_catches_the_pipeline(self):
        self.assertEqual(publish.audit(["pipeline/refresh.py"]),
                         ["pipeline/refresh.py"])

    def test_audit_catches_private_notes(self):
        self.assertEqual(publish.audit(["internal/SPLIT.md", "outreach/README.md"]),
                         ["internal/SPLIT.md", "outreach/README.md"])

    def test_audit_allows_ordinary_public_paths(self):
        self.assertEqual(publish.audit(["index.html", "data/sponsors.json",
                                        "london/index.html"]), [])
