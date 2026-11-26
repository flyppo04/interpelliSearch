"""Test su pagine salvate (tests/fixtures). Lancio: python -m unittest"""
import unittest
from pathlib import Path

from watcher import fetch, filters, sources

FIXTURES = Path(__file__).parent / "fixtures"
RULES = {"must_any": ["interpell", "supplenz"],
         "classes": {"A041": ["A041", "A41"], "B016": ["B016", "B16", "laboratorio di informatica"], "AR02": ["AR02"]},
         "other": ["informatic"],
         "exclude_any": ["esit", "graduatoria definitiva", "individuat"]}


class TestRss(unittest.TestCase):
    def setUp(self):
        body = (FIXTURES / "ustms_feed.xml").read_bytes()
        self.items = list(sources.parse_rss(body, "https://www.ustms.it/"))

    def test_reads_all_items(self):
        self.assertEqual(len(self.items), 10)
        first = self.items[0]
        self.assertEqual(first["titolo"], "LUCCA – INTERPELLO PER SUPPLENZA A041- 16h settimanali")
        self.assertEqual(first["url"], "https://www.ustms.it/?p=9141")  # link breve, senza titolo
        self.assertEqual(first["data"], "2026-11-24")

    def test_filter_keeps_a041_only(self):
        kept = [i["titolo"] for i in self.items if filters.classes(f"{i['titolo']} {i['testo']}", RULES)]
        self.assertIn("LUCCA – INTERPELLO PER SUPPLENZA A041- 16h settimanali", kept)
        self.assertIn("I.T.C. ZACCAGNA: INTERPELLO CLASSE DI CONCORSO A041", kept)
        self.assertNotIn("IC MORATTI-BONOMI: Interpello c.d.c. EEEE – sede Monzone", kept)


class TestHtml(unittest.TestCase):
    def test_collects_links(self):
        body = (FIXTURES / "scuola_interpelli.html").read_bytes()
        items = list(sources.parse_html(body, "https://scuola.example.it/interpelli/"))
        titles = [i["titolo"] for i in items]
        self.assertIn("Interpello cl. di concorso A041 – SCIENZE E TECNOLOGIE INFORMATICHE", titles)
        self.assertIn("https://scuola.example.it/interpello-a041/", [i["url"] for i in items])  # link relativo risolto
        self.assertIn("Interpello cl. di concorso A040 – ELETTRONICA", titles)  # testo dentro <b> incluso
        self.assertEqual(len(items), 3)  # Home + 2 interpelli: duplicati e link senza testo scartati


class TestRobots(unittest.TestCase):
    URL = "https://sito.example/pagina"

    def test_two_groups_one_forbids(self):
        # caso reale: un blocco permette tutto, un secondo blocco aggiunto dal gestore vieta tutto
        lines = ["User-agent: *", "Allow: /", "", "User-agent: GPTBot", "Disallow: /", "",
                 "User-agent: *", "Disallow: /", "Allow: /presentazione/"]
        self.assertFalse(fetch.robots_allow(lines, self.URL))

    def test_only_other_bots_forbidden(self):
        lines = ["User-agent: GPTBot", "Disallow: /", "", "User-agent: *", "Disallow: /wp-admin/"]
        self.assertTrue(fetch.robots_allow(lines, self.URL))
        self.assertFalse(fetch.robots_allow(lines, "https://sito.example/wp-admin/x"))

    def test_missing_robots(self):
        self.assertTrue(fetch.robots_allow([], self.URL))


class TestFilters(unittest.TestCase):
    def test_cases(self):
        c = lambda text: filters.classes(text, RULES)
        self.assertEqual(c("Interpello classe A-041 - assenza doc. Mario Rossi"), ["A041"])
        self.assertEqual(c("Interpello ITP classe di concorso B-016"), ["B016"])
        self.assertEqual(c("Interpello assistente tecnico area AR02"), ["AR02"])
        self.assertEqual(c("Avviso supplenza Informatica"), ["informatica, classe da verificare"])
        self.assertEqual(c("Interpello assistente tecnico area AR23"), [])
        self.assertEqual(c("Interpello A040 elettronica"), [])
        self.assertEqual(c("Esito interpello A041"), [])
        self.assertEqual(c("Orario lezioni A041"), [])

    def test_empty_rules_keep_everything(self):
        self.assertTrue(filters.classes("qualsiasi cosa", {}))


if __name__ == "__main__":
    unittest.main()
