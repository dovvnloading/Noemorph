"""Protect the simplified public homepage without weakening research access."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2] / "public-site" / "dist"

class PublicLandingUxTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (ROOT / "index.html").read_text(encoding="utf-8")
        cls.app = (ROOT / "app.js").read_text(encoding="utf-8")
        cls.css = (ROOT / "styles.css").read_text(encoding="utf-8")

    def test_search_first_and_catalog_before_optional_features(self):
        html = self.html
        self.assertEqual(html.count('id="search"'), 1)
        self.assertIn('id="hero-search-form"', html)
        self.assertLess(html.index('id="top"'), html.index('id="catalog"'))
        self.assertLess(html.index('id="catalog"'), html.index('id="discover"'))
        self.assertLess(html.index('id="catalog"'), html.index('id="atlas"'))
        self.assertIn('id="hero-record-count"', html)

    def test_optional_tools_are_collapsed_but_deep_linkable(self):
        html = self.html
        for marker in ('id="discovery-disclosure"', 'id="atlas-disclosure"',
                       'href="#discover"', 'href="#atlas"', 'id="atlas-svg"',
                       'id="discovery-stage"'):
            self.assertIn(marker, html)
        self.assertNotIn('id="discovery-disclosure" open', html)
        self.assertNotIn('id="atlas-disclosure" open', html)
        self.assertIn('disclosure.open = true', (ROOT / "discovery.js").read_text())
        self.assertIn('disclosure.open = true', (ROOT / "atlas.js").read_text())

    def test_assets_loaded_exactly_once(self):
        for name in ("app.js", "discovery.js", "atlas.js"):
            self.assertEqual(self.html.count('src="' + name + '"'), 1)
        for name in ("styles.css", "discovery.css", "atlas.css"):
            self.assertEqual(self.html.count('href="' + name + '"'), 1)

    def test_catalog_still_has_deeper_research_and_citations(self):
        self.assertIn('record-summary-text', self.app)
        self.assertIn('record-depth', self.app)
        self.assertIn('Explore research notes and sources', self.app)
        self.assertIn('claimReviewHtml(r)', self.app)
        self.assertIn('exportCitations(record)', self.app)
        self.assertIn('No theory-to-theory links', self.html)
        self.assertIn('Inclusion is not endorsement', self.html)
        self.assertIn('prefers-reduced-motion', self.css)

    def test_extra_showcase_sections_do_not_reappear(self):
        for obsolete in ('class="hero-art"', 'class="principles"',
                         'class="intro section-wrap"', 'class="participate"'):
            self.assertNotIn(obsolete, self.html)

if __name__ == "__main__":
    unittest.main()
