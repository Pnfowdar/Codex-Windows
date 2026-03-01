import re
import unittest
from pathlib import Path

from repair_local_threads import canonicalize_workspace_root


RUN_PS1_PATH = Path(__file__).resolve().parent / "scripts" / "run.ps1"


def load_runps1_normalizer():
    source = RUN_PS1_PATH.read_text(encoding="utf-8")
    match = re.search(
        r"(def normalize_windows_root\(value\):\r?\n.*?)(?=\r?\ndef normalize_root_list)",
        source,
        flags=re.DOTALL,
    )
    if not match:
        raise AssertionError("Could not locate normalize_windows_root in scripts/run.ps1")

    namespace = {}
    exec(match.group(1), namespace)
    return namespace["normalize_windows_root"]


class ThreadPathNormalizationTests(unittest.TestCase):
    def test_repair_script_canonicalizes_drive_paths(self):
        self.assertEqual(canonicalize_workspace_root(r"D:\Projects\Codex-Windows"), r"\\?\D:\Projects\Codex-Windows")
        self.assertEqual(canonicalize_workspace_root(r"d:\projects"), r"\\?\D:\projects")
        self.assertEqual(canonicalize_workspace_root(r"\\?\d:\projects"), r"\\?\D:\projects")

    def test_repair_script_keeps_unc_long_path(self):
        self.assertEqual(
            canonicalize_workspace_root(r"\\?\UNC\server\share\repo"),
            r"\\?\UNC\server\share\repo",
        )

    def test_runps1_embedded_normalizer_matches_canonical_format(self):
        normalize_windows_root = load_runps1_normalizer()
        self.assertEqual(normalize_windows_root(r"D:\Projects\Codex-Windows"), r"\\?\D:\Projects\Codex-Windows")
        self.assertEqual(normalize_windows_root(r"d:\projects"), r"\\?\D:\projects")
        self.assertEqual(normalize_windows_root(r"\\?\d:\projects"), r"\\?\D:\projects")
        self.assertEqual(
            normalize_windows_root(r"\\?\UNC\server\share\repo"),
            r"\\?\UNC\server\share\repo",
        )


if __name__ == "__main__":
    unittest.main()
