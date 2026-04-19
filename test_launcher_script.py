import re
import unittest
from pathlib import Path


RUN_PS1_PATH = Path(__file__).resolve().parent / "scripts" / "run.ps1"


class LauncherScriptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = RUN_PS1_PATH.read_text(encoding="utf-8")

    def test_latest_dmg_url_is_pinned_in_launcher(self):
        self.assertIn(
            "https://persistent.oaistatic.com/codex-app-prod/Codex.dmg",
            self.source,
        )
        self.assertRegex(self.source, r"function Get-LatestDmgUrl\(\)")

    def test_user_data_dir_is_versioned_by_launch_storage_tag(self):
        self.assertRegex(
            self.source,
            r'userdata-\$profileSuffix-\$launchStorageTag',
        )
        self.assertRegex(
            self.source,
            r'cache-\$profileSuffix-\$launchStorageTag',
        )
        self.assertRegex(self.source, r"function Get-LaunchStorageTag\(\[object\]\$Pkg\)")

    def test_launcher_sets_distinct_electron_identity_overrides(self):
        self.assertRegex(self.source, r"function Update-BootstrapIdentity\(\[string\]\$AppDir\)")
        self.assertIn("CODEX_ELECTRON_APP_NAME", self.source)
        self.assertIn("CODEX_ELECTRON_APP_ID", self.source)
        self.assertIn("CODEX_ELECTRON_USER_DATA_PATH", self.source)
        self.assertRegex(self.source, r"function Get-LauncherAppIdentity\(\[string\]\$ProfileSuffix\)")
        self.assertIn("com.openai.codex.launcher.", self.source)


if __name__ == "__main__":
    unittest.main()
