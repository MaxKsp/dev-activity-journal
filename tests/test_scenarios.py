"""Testes reproduzíveis de regras e cenários, sem depender de arquivos pré-gerados."""
import json
import tempfile
import unittest
from pathlib import Path

from generate_scenarios import build_case, generate
from scenario_rules import evaluate, phone_e164, retry_delay, sla_status, message_mode


class ScenariosTests(unittest.TestCase):
    def test_explicit_edge_cases(self):
        self.assertEqual(phone_e164("+55 (11) 91234-5678"), "5511912345678")
        self.assertEqual(phone_e164("11 3456 7890"), "551134567890")
        self.assertIsNone(phone_e164("123"))
        self.assertEqual(retry_delay(1, 5, 300), 5)
        self.assertEqual(retry_delay(20, 5, 300), 300)
        self.assertEqual(sla_status(120, 120), "overdue")
        self.assertEqual(sla_status(91, 120, 30), "warning")
        self.assertEqual(sla_status(20, 120, 30), "healthy")
        self.assertEqual(message_mode(1440), "session")
        self.assertEqual(message_mode(1441), "template")

    def test_412_scenarios_are_unique_and_correct(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            paths = generate(412, folder)
            self.assertEqual(len(paths), 412)
            ids, unique_payloads = set(), set()
            for path in paths:
                with self.subTest(case=path.name):
                    obj = json.loads(path.read_text(encoding="utf-8"))
                    self.assertNotIn(obj["id"], ids)
                    ids.add(obj["id"])
                    key = json.dumps([obj["category"], obj["input"]], sort_keys=True)
                    self.assertNotIn(key, unique_payloads, "Cenário duplicado")
                    unique_payloads.add(key)
                    self.assertEqual(evaluate(obj["category"], obj["input"]), obj["expected"])
                    self.assertEqual(obj, build_case(int(obj["id"].split("-")[1])))
            self.assertEqual(generate(412, folder), paths)

    def test_invalid_scenario_count(self):
        with tempfile.TemporaryDirectory() as temp:
            for value in (0, -1, 10001):
                with self.subTest(value=value), self.assertRaises(ValueError):
                    generate(value, Path(temp))


if __name__ == "__main__":
    unittest.main()
