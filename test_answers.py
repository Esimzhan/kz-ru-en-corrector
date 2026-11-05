import ast
import json
from pathlib import Path
import tempfile
import threading
import types
import unittest
from unittest.mock import Mock

from answers import answer_request, MAX_REFERENCE_BYTES


class ReferenceTests(unittest.TestCase):
    def test_reloads_references_and_handles_empty_folder(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            prompt, payload = answer_request("Question?", short=True, directory=directory)
            self.assertIn("general knowledge", prompt)
            self.assertIn("AND its full answer text", prompt)
            self.assertIn("check the result and option mapping", prompt)
            self.assertEqual(json.loads(payload)["references"], [])
            note = directory / "notes.md"
            note.write_text("Жауап: 42", encoding="utf-8")
            (directory / "ignored.txt").write_text("not a reference")
            (directory / "link.md").symlink_to(note)
            prompt, payload = answer_request("Сұрақ?", directory=directory)
            self.assertIn("ONLY", prompt)
            self.assertNotIn("1–3 short sentences", prompt)
            self.assertEqual(json.loads(payload)["references"],
                             [{"file": "notes.md", "text": "Жауап: 42"}])
            note.write_text("New answer", encoding="utf-8")
            _, payload = answer_request("Question?", directory=directory)
            self.assertEqual(json.loads(payload)["references"][0]["text"], "New answer")

    def test_invalid_or_oversized_files_fail(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            note = directory / "notes.md"
            note.write_bytes(b"\xff")
            with self.assertRaisesRegex(ValueError, "UTF-8"):
                answer_request("Q", directory=directory)
            note.write_bytes(b"x" * (MAX_REFERENCE_BYTES + 1))
            with self.assertRaisesRegex(ValueError, "512 KB"):
                answer_request("Q", directory=directory)


class HotkeyTests(unittest.TestCase):
    def setUp(self):
        # Load the real handlers without importing tray/display or redirecting test output.
        tree = ast.parse(Path(__file__).with_name("app_linux.py").read_text())
        wanted = {"clear_answer_grab", "arm_answer_grab", "_on_key", "_handle_key"}
        tree.body = [node for node in tree.body
                     if isinstance(node, ast.FunctionDef) and node.name in wanted]
        self.now = 100.0
        self.state = dict(
            threading=Mock(Timer=Mock()), time=types.SimpleNamespace(monotonic=lambda: self.now),
            xdisp=Mock(), X=types.SimpleNamespace(LockMask=2, Mod2Mask=16, ControlMask=4,
                                                 GrabModeAsync=1, CurrentTime=0),
            KC_A=38, KC_S=39, KC_Z=52, CTRL_KEYS={37, 105}, ALT_KEYS={64, 108},
            DOUBLE_TAP_SECONDS=0.4, _sequence_lock=threading.RLock(),
            _sequence_timer=None, _last_ctrl_a=0.0, _down=set(), _released_at={},
            start_correction=Mock(), log_debug=Mock())
        exec(compile(tree, "app_linux.py", "exec"), self.state)
        self.tick = 0

    def key(self, code, down=True):
        self.tick += 1
        self.state["_on_key"](down, code, self.tick)

    def prefix(self):
        self.key(37)
        self.key(38)
        self.key(38, False)

    def test_short_answer_and_existing_shortcuts(self):
        self.prefix()
        self.key(39)
        self.state["start_correction"].assert_called_once_with("Ctrl+A+S")
        self.state["xdisp"].ungrab_keyboard.assert_called_once()
        self.setUp()
        self.prefix()
        self.key(38)
        self.state["start_correction"].assert_called_once_with("Ctrl+A+A")
        self.setUp()
        for code in [37, 64, 52]:
            self.key(code)
        self.state["start_correction"].assert_called_once_with("Ctrl+Alt+Z")

    def test_no_false_triggers(self):
        for scenario in ["plain_save", "timeout", "ctrl_released", "other_key", "repeat"]:
            with self.subTest(scenario=scenario):
                self.setUp()
                if scenario == "plain_save":
                    self.key(37)
                else:
                    self.prefix()
                    if scenario == "timeout":
                        self.now += 1
                        self.state["clear_answer_grab"]()
                    elif scenario == "ctrl_released":
                        self.key(37, False)
                        self.key(37)
                    elif scenario == "other_key":
                        self.key(54)
                    elif scenario == "repeat":
                        self.key(38)
                        self.state["start_correction"].reset_mock()
                        self.key(38)
                self.key(39)
                self.state["start_correction"].assert_not_called()

    def test_old_timer_cannot_clear_new_sequence(self):
        self.prefix()
        old = self.state["_last_ctrl_a"]
        self.state["clear_answer_grab"]()
        self.now += 1
        self.key(38)
        self.state["clear_answer_grab"](old)
        self.key(39)
        self.state["start_correction"].assert_called_once_with("Ctrl+A+S")


if __name__ == "__main__":
    unittest.main()
