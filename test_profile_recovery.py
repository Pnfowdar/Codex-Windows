import base64
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from profile_repair import apply_profile_recovery, choose_recovery_source, remap_profile_path


def make_jwt(email: str) -> str:
    header = base64.urlsafe_b64encode(json.dumps({"alg": "none"}).encode("utf-8")).decode("ascii").rstrip("=")
    payload = base64.urlsafe_b64encode(
        json.dumps(
            {
                "email": email,
                "https://api.openai.com/profile": {
                    "email": email,
                    "email_verified": True,
                },
            }
        ).encode("utf-8")
    ).decode("ascii").rstrip("=")
    return f"{header}.{payload}."


def write_auth(root: Path, email: str) -> None:
    auth = {
        "auth_mode": "chatgpt",
        "tokens": {
            "id_token": make_jwt(email),
            "access_token": make_jwt(email),
        },
    }
    (root / "auth.json").write_text(json.dumps(auth), encoding="utf-8")


def write_installation_id(root: Path, installation_id: str) -> None:
    (root / "installation_id").write_text(installation_id, encoding="utf-8")


def write_state(root: Path, thread_ids: list[str], cwd_prefix: str = r"\\?\D:\Projects\Test") -> None:
    db = root / "state_5.sqlite"
    conn = sqlite3.connect(db)
    conn.execute(
        """
        CREATE TABLE threads (
            id TEXT PRIMARY KEY,
            rollout_path TEXT NOT NULL,
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL,
            source TEXT NOT NULL,
            model_provider TEXT NOT NULL,
            cwd TEXT NOT NULL,
            title TEXT NOT NULL,
            sandbox_policy TEXT NOT NULL,
            approval_mode TEXT NOT NULL,
            tokens_used INTEGER NOT NULL DEFAULT 0,
            has_user_event INTEGER NOT NULL DEFAULT 0,
            archived INTEGER NOT NULL DEFAULT 0,
            archived_at INTEGER,
            git_sha TEXT,
            git_branch TEXT,
            git_origin_url TEXT,
            cli_version TEXT NOT NULL DEFAULT '',
            first_user_message TEXT NOT NULL DEFAULT '',
            agent_nickname TEXT,
            agent_role TEXT,
            memory_mode TEXT NOT NULL DEFAULT 'enabled',
            model TEXT,
            reasoning_effort TEXT,
            agent_path TEXT,
            created_at_ms INTEGER,
            updated_at_ms INTEGER
        )
        """
    )
    for index, thread_id in enumerate(thread_ids, start=1):
        conn.execute(
            """
            INSERT INTO threads (
                id, rollout_path, created_at, updated_at, source, model_provider, cwd, title,
                sandbox_policy, approval_mode, first_user_message
            )
            VALUES (?, ?, ?, ?, 'desktop', 'openai', ?, ?, 'danger-full-access', 'never', ?)
            """,
            (
                thread_id,
                str(root / "sessions" / f"{thread_id}.jsonl"),
                index,
                index,
                cwd_prefix,
                f"title-{thread_id}",
                f"prompt-{thread_id}",
            ),
        )
    conn.commit()
    conn.close()


def write_session(root: Path, thread_id: str) -> None:
    sessions = root / "sessions"
    sessions.mkdir(parents=True, exist_ok=True)
    (sessions / f"{thread_id}.jsonl").write_text(f'{{"thread_id":"{thread_id}"}}\n', encoding="utf-8")


def write_global_state(root: Path, roots: list[str]) -> None:
    payload = {
        "electron-saved-workspace-roots": roots,
        "active-workspace-roots": roots[:1],
        "electron-workspace-root-labels": {value: value.split("\\")[-1] for value in roots},
        "electron-persisted-atom-state": {
            "electron-saved-workspace-roots": roots,
            "active-workspace-roots": roots[:1],
            "electron-workspace-root-labels": {value: value.split("\\")[-1] for value in roots},
        },
    }
    (root / ".codex-global-state.json").write_text(json.dumps(payload), encoding="utf-8")


class ProfileRecoveryTests(unittest.TestCase):
    def test_remap_profile_path_preserves_windows_long_path_prefix(self):
        source = Path(r"C:\Users\pnfow\.codex-personal-store")
        dest = Path(r"C:\Users\pnfow\.codex")
        original = r"\\?\C:\Users\pnfow\.codex-personal-store\sessions\2026\04\18\rollout.jsonl"
        expected = r"\\?\C:\Users\pnfow\.codex\sessions\2026\04\18\rollout.jsonl"
        self.assertEqual(expected, remap_profile_path(original, source, dest))

    def test_choose_recovery_source_prefers_matching_personal_identity(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            personal = temp / ".codex"
            work = temp / ".codex-work"
            personal_store = temp / ".codex-personal-store"
            work_clone = temp / ".codex-windows-personal"
            for root in (personal, work, personal_store, work_clone):
                root.mkdir(parents=True)

            write_auth(personal, "philipf@gria.com.au")
            write_installation_id(personal, "personal-new")
            write_state(personal, ["p-current"])

            write_auth(work, "marketing@gsvets.com.au")
            write_installation_id(work, "work-shared")
            write_state(work, [f"w-{i}" for i in range(20)])

            write_auth(personal_store, "philipf@gria.com.au")
            write_installation_id(personal_store, "personal-old")
            write_state(personal_store, [f"p-{i}" for i in range(200)])

            write_auth(work_clone, "marketing@gsvets.com.au")
            write_installation_id(work_clone, "work-shared")
            write_state(work_clone, [f"c-{i}" for i in range(220)])

            decision = choose_recovery_source(personal, work, [personal_store, work_clone])

            self.assertIsNotNone(decision)
            self.assertEqual(personal_store, decision.source_root)
            self.assertEqual("philipf@gria.com.au", decision.source_email)

    def test_apply_profile_recovery_merges_threads_and_preserves_identity(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            dest = temp / ".codex"
            source = temp / ".codex-personal-store"
            for root in (dest, source):
                root.mkdir(parents=True)

            write_auth(dest, "philipf@gria.com.au")
            write_installation_id(dest, "personal-current")
            write_state(dest, ["current-thread"])
            write_session(dest, "current-thread")
            write_global_state(dest, [r"\\?\D:\Projects\Codex-Windows"])

            write_auth(source, "philipf@gria.com.au")
            write_installation_id(source, "personal-legacy")
            write_state(source, ["legacy-a", "legacy-b"])
            write_session(source, "legacy-a")
            write_session(source, "legacy-b")
            write_global_state(source, [r"\\?\D:\Projects\OptionsMatrix", r"\\?\D:\Projects\Codex-Windows"])

            result = apply_profile_recovery(source, dest)

            self.assertTrue(result["applied"])
            self.assertEqual(2, result["threads_added"])
            self.assertEqual(2, result["sessions_copied"])
            self.assertEqual("personal-current", (dest / "installation_id").read_text(encoding="utf-8"))
            auth_payload = json.loads((dest / "auth.json").read_text(encoding="utf-8"))
            self.assertEqual("chatgpt", auth_payload["auth_mode"])

            conn = sqlite3.connect(dest / "state_5.sqlite")
            thread_ids = {row[0] for row in conn.execute("SELECT id FROM threads")}
            conn.close()
            self.assertEqual({"current-thread", "legacy-a", "legacy-b"}, thread_ids)

            merged_state = json.loads((dest / ".codex-global-state.json").read_text(encoding="utf-8"))
            saved_roots = merged_state["electron-saved-workspace-roots"]
            self.assertIn(r"\\?\D:\Projects\Codex-Windows", saved_roots)
            self.assertIn(r"\\?\D:\Projects\OptionsMatrix", saved_roots)


if __name__ == "__main__":
    unittest.main()
