import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from journal import add_entry, daily_prompt, report


class JournalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_daily_prompt_is_idempotent(self):
        today = date(2026, 10, 29)
        self.assertTrue(daily_prompt(self.root, today))
        self.assertFalse(daily_prompt(self.root, today))
        prompts = list((self.root / "challenges").glob("*.md"))
        self.assertEqual(len(prompts), 1)
        self.assertIn("Critério mínimo de aceite", prompts[0].read_text(encoding="utf-8"))

    def test_report_is_changed_only_when_data_changes(self):
        self.assertTrue(report(self.root))
        self.assertFalse(report(self.root))
        add_entry(self.root, "Trivya", "Corrigido filtro de horários")
        self.assertTrue(report(self.root))
        self.assertFalse(report(self.root))
        self.assertIn("Trivya: 1", (self.root / "reports" / "summary.md").read_text(encoding="utf-8"))

    def test_rejects_empty_or_insufficient_records(self):
        with self.assertRaises(ValueError):
            add_entry(self.root, "P", "abc")
        self.assertFalse((self.root / "data" / "entries.jsonl").exists())

    def test_entry_is_valid_json_and_has_timestamp(self):
        add_entry(self.root, "Orbita", "Adicionados testes para importação")
        entries = (self.root / "data" / "entries.jsonl").read_text(encoding="utf-8").splitlines()
        record = json.loads(entries[0])
        self.assertEqual(record["project"], "Orbita")
        self.assertIn("date", record)


if __name__ == "__main__":
    unittest.main()
