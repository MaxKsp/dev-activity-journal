"""Verifica o observador sem disparar publicações remotas."""
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from scripts import publish_watcher as watcher


class WatcherTests(unittest.TestCase):
    def setUp(self):
        self.day = date(2026, 10, 29)

    def test_reject_too_short_interval(self):
        with self.assertRaises(ValueError):
            watcher.run(435, 9, self.day, 21, once=True, publish=False)

    def test_private_profile_count_fallback_allows_valid_delivery(self):
        with patch.object(watcher, "verify_repository"), \
             patch.object(watcher, "today_brazil", return_value=self.day), \
             patch.object(watcher, "contribution_count", return_value=0), \
             patch.object(watcher, "ready_files", return_value=[Path("publication_queue/a.md")]), \
             patch.object(watcher, "publish_one", return_value="Publicado: publication_queue/a.md") as publish:
            watcher.run(435, 10, self.day, 24, once=True, publish=True)
            publish.assert_called_once_with(Path("publication_queue/a.md"))

    def test_goal_reached_never_publishes(self):
        with patch.object(watcher, "verify_repository"), \
             patch.object(watcher, "today_brazil", return_value=self.day), \
             patch.object(watcher, "contribution_count", return_value=435), \
             patch.object(watcher, "publish_one") as publish:
            watcher.run(435, 10, self.day, 21, once=True, publish=True)
            publish.assert_not_called()

    def test_invalid_date_never_publishes(self):
        with patch.object(watcher, "verify_repository"), \
             patch.object(watcher, "today_brazil", return_value=date(2026, 10, 30)), \
             patch.object(watcher, "contribution_count") as count:
            watcher.run(435, 10, self.day, 21, once=True, publish=True)
            count.assert_not_called()

    def test_one_valid_delivery_per_cycle(self):
        with patch.object(watcher, "verify_repository"), \
             patch.object(watcher, "today_brazil", return_value=self.day), \
             patch.object(watcher, "contribution_count", return_value=21), \
             patch.object(watcher, "ready_files", return_value=[
                 Path("publication_queue/one.md"), Path("publication_queue/two.md")
             ]), \
             patch.object(watcher, "publish_one", return_value="Publicado") as publish:
            watcher.run(435, 10, self.day, 21, once=True, publish=True)
            publish.assert_called_once_with(Path("publication_queue/one.md"))

    def test_queue_filters_tiny_unchanged_and_other_extensions(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            queue = root / "publication_queue"
            queue.mkdir()
            (queue / "a.md").write_text("Registro validado: " + ("x" * 90), encoding="utf-8")
            (queue / "b.md").write_text("curto", encoding="utf-8")
            (queue / "c.md").write_text("Documento sem alterações desde o último commit " + ("y" * 90), encoding="utf-8")
            (queue / ".env").write_text("KEY=" + ("x" * 90), encoding="utf-8")
            def status(args):
                return "" if args[-1].endswith("c.md") else "??"
            with patch.object(watcher, "ROOT", root), patch.object(watcher, "QUEUE", queue), patch.object(watcher, "call", side_effect=status):
                self.assertEqual([x.name for x in watcher.ready_files()], ["a.md"])


if __name__ == "__main__":
    unittest.main()
