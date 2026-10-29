"""Testes do publicador incremental de cenários de regressão."""
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from scripts import case_campaign as campaign
from scenario_rules import evaluate


class CampaignTests(unittest.TestCase):
    def test_no_more_commits_at_target(self):
        with patch.object(campaign, "check_date", return_value=True), \
             patch.object(campaign, "verify_repository"), \
             patch.object(campaign, "synced_with_remote", return_value=True), \
             patch.object(campaign, "estimated_total", return_value=435), \
             patch.object(campaign, "publish_one") as publish:
            self.assertEqual(campaign.cycle(435, 30, "sha", date(2026, 10, 29)),
                             "STOP_LIMITE_LOCAL 435/435")
            publish.assert_not_called()

    def test_stops_if_utc_day_ends(self):
        with patch.object(campaign, "check_date", return_value=False), \
             patch.object(campaign, "publish_one") as publish:
            self.assertEqual(campaign.cycle(435, 30, "sha", date(2026, 10, 29)),
                             "STOP_DATA_UTC")
            publish.assert_not_called()

    def test_will_not_publish_if_remote_not_synced(self):
        with patch.object(campaign, "check_date", return_value=True), \
             patch.object(campaign, "verify_repository"), \
             patch.object(campaign, "synced_with_remote", return_value=False), \
             patch.object(campaign, "publish_one") as publish:
            self.assertEqual(campaign.cycle(435, 30, "sha", date(2026, 10, 29)),
                             "WAIT_SYNC")
            publish.assert_not_called()

    def test_single_case_per_cycle(self):
        path = Path("publication_queue/SC-0001.json")
        with patch.object(campaign, "check_date", return_value=True), \
             patch.object(campaign, "verify_repository"), \
             patch.object(campaign, "synced_with_remote", return_value=True), \
             patch.object(campaign, "estimated_total", side_effect=[30, 31]), \
             patch.object(campaign, "pending_or_next_case", return_value=path), \
             patch.object(campaign, "publish_one", return_value="Publicado: publication_queue/SC-0001.json") as publish:
            self.assertIn("ESTIMATIVA 31/435", campaign.cycle(435, 30, "sha", date(2026, 10, 29)))
            publish.assert_called_once_with(path)

    def test_generation_is_deterministic_and_valid(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            queue = root / "publication_queue"
            with patch.object(campaign, "ROOT", root), \
                 patch.object(campaign, "QUEUE", queue), \
                 patch.object(campaign, "tracked", return_value=False):
                first = campaign.pending_or_next_case()
                self.assertIsNotNone(first)
                obj = json.loads(first.read_text(encoding="utf-8"))
                self.assertEqual(obj["id"], "SC-0001")
                self.assertEqual(evaluate(obj["category"], obj["input"]), obj["expected"])
                self.assertEqual(campaign.pending_or_next_case(), first)
                self.assertEqual(json.loads(first.read_text(encoding="utf-8")), obj)


if __name__ == "__main__":
    unittest.main()
