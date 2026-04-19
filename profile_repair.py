from __future__ import annotations

import argparse
import base64
import json
import shutil
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


SPARSE_THREAD_THRESHOLD = 25
MIN_THREAD_GAIN = 20


@dataclass(frozen=True)
class ProfileSnapshot:
    root: Path
    email: str | None
    installation_id: str | None
    thread_count: int


@dataclass(frozen=True)
class RecoveryDecision:
    source_root: Path
    source_email: str | None
    source_thread_count: int
    target_thread_count: int
    reason: str


def _decode_jwt_payload(token: str | None) -> dict[str, object]:
    if not token or "." not in token:
        return {}
    parts = token.split(".")
    if len(parts) < 2 or not parts[1]:
        return {}
    payload = parts[1]
    payload += "=" * (-len(payload) % 4)
    try:
        decoded = base64.urlsafe_b64decode(payload.encode("ascii"))
        data = json.loads(decoded.decode("utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def read_auth_email(root: Path) -> str | None:
    auth_path = root / "auth.json"
    if not auth_path.exists():
        return None
    try:
        data = json.loads(auth_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    tokens = data.get("tokens")
    if not isinstance(tokens, dict):
        return None
    for token_name in ("access_token", "id_token"):
        payload = _decode_jwt_payload(tokens.get(token_name))
        email = payload.get("email")
        if isinstance(email, str) and email.strip():
            return email.strip().lower()
        profile = payload.get("https://api.openai.com/profile")
        if isinstance(profile, dict):
            profile_email = profile.get("email")
            if isinstance(profile_email, str) and profile_email.strip():
                return profile_email.strip().lower()
    return None


def read_installation_id(root: Path) -> str | None:
    path = root / "installation_id"
    if not path.exists():
        return None
    value = path.read_text(encoding="utf-8").strip()
    return value or None


def find_state_db(root: Path) -> Path | None:
    for index in range(10, -1, -1):
        candidate = root / f"state_{index}.sqlite"
        if candidate.exists():
            return candidate
    return None


def count_threads(root: Path) -> int:
    db_path = find_state_db(root)
    if not db_path:
        return 0
    try:
        conn = sqlite3.connect(db_path)
        count = conn.execute("SELECT count(*) FROM threads").fetchone()[0]
        conn.close()
        return int(count)
    except Exception:
        return 0


def snapshot_profile(root: Path) -> ProfileSnapshot:
    return ProfileSnapshot(
        root=root,
        email=read_auth_email(root),
        installation_id=read_installation_id(root),
        thread_count=count_threads(root),
    )


def _windows_path_variants(root: Path) -> list[str]:
    raw = str(root).replace("/", "\\")
    variants = [raw]
    if len(raw) >= 3 and raw[1] == ":" and raw[2] == "\\":
        variants.insert(0, f"\\\\?\\{raw}")
    return variants


def count_rollout_paths_for_source(target_root: Path, source_root: Path) -> int:
    db_path = find_state_db(target_root)
    if not db_path:
        return 0
    variants = _windows_path_variants(source_root)
    conn = sqlite3.connect(db_path)
    try:
        count = 0
        for variant in variants:
            count += int(
                conn.execute(
                    "SELECT count(*) FROM threads WHERE lower(rollout_path) LIKE lower(?)",
                    (variant + "%",),
                ).fetchone()[0]
            )
        return count
    finally:
        conn.close()


def choose_recovery_source(target_root: Path, work_root: Path, candidate_roots: list[Path]) -> RecoveryDecision | None:
    target = snapshot_profile(target_root)
    work = snapshot_profile(work_root)
    best: RecoveryDecision | None = None
    for candidate_root in candidate_roots:
        if not candidate_root.exists():
            continue
        candidate = snapshot_profile(candidate_root)
        if target.email and candidate.email and candidate.email != target.email:
            continue
        if work.email and candidate.email and candidate.email == work.email:
            continue
        if work.installation_id and candidate.installation_id and candidate.installation_id == work.installation_id:
            continue
        rollout_path_refs = count_rollout_paths_for_source(target_root, candidate_root)
        sparse_target = target.thread_count < SPARSE_THREAD_THRESHOLD
        has_substantial_history_gain = (
            candidate.thread_count > target.thread_count
            and candidate.thread_count >= max(SPARSE_THREAD_THRESHOLD, target.thread_count + MIN_THREAD_GAIN)
        )
        if not ((sparse_target and has_substantial_history_gain) or rollout_path_refs > 0):
            continue
        reason = (
            "repair rollout paths still pointing at legacy personal store"
            if rollout_path_refs > 0
            else "matching identity with substantially richer local history"
        )
        decision = RecoveryDecision(
            source_root=candidate.root,
            source_email=candidate.email,
            source_thread_count=candidate.thread_count,
            target_thread_count=target.thread_count,
            reason=reason,
        )
        if not best or decision.source_thread_count > best.source_thread_count:
            best = decision
    return best


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def _backup_file(path: Path) -> str | None:
    if not path.exists():
        return None
    backup = path.with_name(f"{path.name}.bak_profile_repair_{_timestamp()}")
    shutil.copy2(path, backup)
    return str(backup)


def _copy_tree_missing_only(source: Path, destination: Path) -> int:
    if not source.exists():
        return 0
    copied = 0
    for item in source.rglob("*"):
        if not item.is_file():
            continue
        relative = item.relative_to(source)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            continue
        shutil.copy2(item, target)
        copied += 1
    return copied


def remap_profile_path(value: str | None, source_root: Path, dest_root: Path) -> str | None:
    if not value:
        return value
    value_norm = value.replace("/", "\\")
    source_variants = _windows_path_variants(source_root)
    dest_variants = _windows_path_variants(dest_root)
    for source_prefix, dest_prefix in zip(source_variants, dest_variants):
        if value_norm.lower().startswith(source_prefix.lower()):
            suffix = value_norm[len(source_prefix) :].lstrip("\\/")
            if suffix:
                return dest_prefix + "\\" + suffix
            return dest_prefix
    return value


def _repair_existing_rollout_paths(dest_root: Path, source_root: Path) -> int:
    dest_db = find_state_db(dest_root)
    if not dest_db:
        return 0
    conn = sqlite3.connect(dest_db)
    try:
        updated = 0
        rows = conn.execute("SELECT id, rollout_path FROM threads").fetchall()
        for thread_id, rollout_path in rows:
            remapped = remap_profile_path(rollout_path, source_root, dest_root)
            if remapped != rollout_path:
                conn.execute("UPDATE threads SET rollout_path = ? WHERE id = ?", (remapped, thread_id))
                updated += 1
        conn.commit()
        return updated
    finally:
        conn.close()


def _table_columns(conn: sqlite3.Connection, table_name: str) -> list[str]:
    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return [str(row[1]) for row in rows]


def _merge_threads(source_root: Path, dest_root: Path) -> tuple[int, str | None]:
    source_db = find_state_db(source_root)
    if not source_db:
        return 0, None
    dest_db = find_state_db(dest_root)
    if not dest_db:
        dest_db = dest_root / source_db.name
        shutil.copy2(source_db, dest_db)
        backup_path = _backup_file(dest_db)
        conn = sqlite3.connect(dest_db)
        try:
            conn.execute(
                "UPDATE threads SET rollout_path = ? WHERE 1 = 0",
                ("",),
            )
        except Exception:
            conn.close()
            raise
        rows = conn.execute("SELECT id, rollout_path FROM threads").fetchall()
        for thread_id, rollout_path in rows:
            remapped = remap_profile_path(rollout_path, source_root, dest_root)
            if remapped != rollout_path:
                conn.execute("UPDATE threads SET rollout_path = ? WHERE id = ?", (remapped, thread_id))
        conn.commit()
        conn.close()
        thread_count = count_threads(dest_root)
        return thread_count, backup_path

    backup_path = _backup_file(dest_db)
    source_conn = sqlite3.connect(source_db)
    dest_conn = sqlite3.connect(dest_db)
    try:
        source_columns = _table_columns(source_conn, "threads")
        dest_columns = _table_columns(dest_conn, "threads")
        shared_columns = [column for column in dest_columns if column in source_columns]
        if not shared_columns:
            return 0, backup_path

        before = dest_conn.execute("SELECT count(*) FROM threads").fetchone()[0]
        column_sql = ", ".join(shared_columns)
        placeholders = ", ".join("?" for _ in shared_columns)
        query = f"SELECT {column_sql} FROM threads ORDER BY updated_at DESC"
        for row in source_conn.execute(query):
            payload = dict(zip(shared_columns, row))
            if "rollout_path" in payload:
                payload["rollout_path"] = remap_profile_path(payload["rollout_path"], source_root, dest_root)
            dest_conn.execute(
                f"INSERT OR IGNORE INTO threads ({column_sql}) VALUES ({placeholders})",
                [payload[column] for column in shared_columns],
            )
        dest_conn.commit()
        after = dest_conn.execute("SELECT count(*) FROM threads").fetchone()[0]
        return int(after - before), backup_path
    finally:
        source_conn.close()
        dest_conn.close()


def _merge_unique_list(*values: object) -> list[object]:
    merged: list[object] = []
    seen: set[str] = set()
    for value in values:
        if not isinstance(value, list):
            continue
        for item in value:
            key = json.dumps(item, sort_keys=True, ensure_ascii=False)
            if key in seen:
                continue
            seen.add(key)
            merged.append(item)
    return merged


def _merge_mapping(*values: object) -> dict[object, object]:
    merged: dict[object, object] = {}
    for value in values:
        if not isinstance(value, dict):
            continue
        merged.update(value)
    return merged


def _merge_global_state(source_root: Path, dest_root: Path) -> tuple[bool, str | None]:
    source_state = source_root / ".codex-global-state.json"
    dest_state = dest_root / ".codex-global-state.json"
    if not source_state.exists():
        return False, None

    if not dest_state.exists():
        shutil.copy2(source_state, dest_state)
        return True, None

    backup_path = _backup_file(dest_state)
    try:
        source_data = json.loads(source_state.read_text(encoding="utf-8"))
    except Exception:
        source_data = {}
    try:
        dest_data = json.loads(dest_state.read_text(encoding="utf-8"))
    except Exception:
        dest_data = {}
    if not isinstance(source_data, dict):
        source_data = {}
    if not isinstance(dest_data, dict):
        dest_data = {}

    source_nested = source_data.get("electron-persisted-atom-state")
    dest_nested = dest_data.get("electron-persisted-atom-state")
    if not isinstance(source_nested, dict):
        source_nested = {}
    if not isinstance(dest_nested, dict):
        dest_nested = {}

    for target, source in ((dest_data, source_data), (dest_nested, source_nested)):
        target["electron-saved-workspace-roots"] = _merge_unique_list(
            target.get("electron-saved-workspace-roots"),
            source.get("electron-saved-workspace-roots"),
        )
        target["active-workspace-roots"] = _merge_unique_list(
            target.get("active-workspace-roots"),
            source.get("active-workspace-roots"),
        )
        target["electron-workspace-root-labels"] = _merge_mapping(
            source.get("electron-workspace-root-labels"),
            target.get("electron-workspace-root-labels"),
        )

    dest_data["electron-persisted-atom-state"] = dest_nested
    dest_state.write_text(json.dumps(dest_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return True, backup_path


def apply_profile_recovery(source_root: Path, dest_root: Path) -> dict[str, object]:
    dest_root.mkdir(parents=True, exist_ok=True)
    threads_added, db_backup = _merge_threads(source_root, dest_root)
    rollout_paths_rewritten = _repair_existing_rollout_paths(dest_root, source_root)
    sessions_copied = _copy_tree_missing_only(source_root / "sessions", dest_root / "sessions")
    archived_sessions_copied = _copy_tree_missing_only(
        source_root / "archived_sessions", dest_root / "archived_sessions"
    )
    global_state_updated, global_state_backup = _merge_global_state(source_root, dest_root)
    return {
        "applied": bool(
            threads_added or rollout_paths_rewritten or sessions_copied or archived_sessions_copied or global_state_updated
        ),
        "source_root": str(source_root),
        "dest_root": str(dest_root),
        "threads_added": threads_added,
        "rollout_paths_rewritten": rollout_paths_rewritten,
        "sessions_copied": sessions_copied,
        "archived_sessions_copied": archived_sessions_copied,
        "db_backup": db_backup,
        "global_state_backup": global_state_backup,
    }


def default_candidate_roots(target_root: Path) -> list[Path]:
    home = target_root.parent
    return [
        home / ".codex-personal-store",
        home / ".codex-windows-personal",
    ]


def run_cli() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-root", required=True)
    parser.add_argument("--work-root", required=True)
    parser.add_argument("--candidate-root", action="append", default=[])
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    target_root = Path(args.target_root)
    work_root = Path(args.work_root)
    candidate_roots = [Path(value) for value in args.candidate_root] or default_candidate_roots(target_root)

    if target_root.name.lower() != ".codex":
        print(json.dumps({"applied": False, "reason": "target is not the personal/native profile"}))
        return 0

    decision = choose_recovery_source(target_root, work_root, candidate_roots)
    if not decision:
        print(json.dumps({"applied": False, "reason": "no recovery source selected"}))
        return 0

    payload: dict[str, object] = {
        "applied": False,
        "selected_source": str(decision.source_root),
        "selected_source_email": decision.source_email,
        "source_thread_count": decision.source_thread_count,
        "target_thread_count": decision.target_thread_count,
        "reason": decision.reason,
    }
    if args.apply:
        payload.update(apply_profile_recovery(decision.source_root, target_root))
        payload["selected_source"] = str(decision.source_root)
        payload["selected_source_email"] = decision.source_email
        payload["source_thread_count"] = decision.source_thread_count
        payload["target_thread_count"] = decision.target_thread_count
        payload["reason"] = decision.reason

    print(json.dumps(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(run_cli())
