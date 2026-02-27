r"""
Repair local Codex thread visibility for Windows desktop profiles.

Actions per profile:
1) Backup `state_5.sqlite` and `.codex-global-state.json`.
2) Normalize `threads.cwd` to a canonical Windows form (`\\?\D:\...`).
3) Backfill empty `first_user_message` values using title or rollout JSONL content.
4) Ensure `.codex-global-state.json` includes nested `thread-titles` and `stage-filter=all`.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import shutil
import sqlite3
from pathlib import Path

PROFILES = [Path.home() / ".codex", Path.home() / ".codex-work"]
ELLIPSIS = "..."


def strip_long_path_prefix(value: str | None) -> str | None:
    if not value:
        return value
    if value.startswith("\\\\?\\"):
        return value[4:]
    return value


def normalize_windows_path(value: str | None) -> str | None:
    if not value:
        return value
    out = strip_long_path_prefix(value)
    out = out.replace("/", "\\")
    if len(out) >= 2 and out[1] == ":":
        out = out[0].upper() + out[1:]
    return out


def canonicalize_workspace_root(value: str | None) -> str | None:
    if value is None:
        return None
    out = value.strip().replace("/", "\\")
    if not out:
        return out
    if out.startswith("\\\\?\\UNC\\"):
        return out
    if out.startswith("\\\\?\\") and len(out) >= 7 and out[4].isalpha() and out[5] == ":" and out[6] == "\\":
        return "\\\\?\\" + out[4].upper() + out[5:]
    if len(out) >= 3 and out[0].isalpha() and out[1] == ":" and out[2] == "\\":
        return "\\\\?\\" + out[0].upper() + out[1:]
    return out


def normalize_root_list(values: object) -> object:
    if not isinstance(values, list):
        return values
    out: list[object] = []
    seen: set[str] = set()
    for value in values:
        normalized = canonicalize_workspace_root(value) if isinstance(value, str) else value
        key = normalized.lower() if isinstance(normalized, str) else str(normalized)
        if key in seen:
            continue
        seen.add(key)
        out.append(normalized)
    return out


def normalize_root_labels(values: object) -> object:
    if not isinstance(values, dict):
        return values
    out: dict[object, object] = {}
    for key, value in values.items():
        normalized_key = canonicalize_workspace_root(key) if isinstance(key, str) else key
        out[normalized_key] = value
    return out


def normalize_cwd_value(value: str | None) -> str | None:
    """Normalize thread cwd to canonical Windows root form used in sidebar filters."""
    return canonicalize_workspace_root(value)


def collapse_whitespace(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def shorten(text: str, limit: int = 180) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - len(ELLIPSIS)].rstrip() + ELLIPSIS


def is_wrapper_message(text: str) -> bool:
    probe = text.strip()
    lower = probe.lower()
    return (
        lower.startswith("# agents.md instructions")
        or lower.startswith("<environment_context>")
        or lower.startswith("<app-context>")
        or lower.startswith("<permissions instructions>")
    )


def read_user_text_from_content(content: object) -> str:
    if isinstance(content, str):
        return collapse_whitespace(content)
    if not isinstance(content, list):
        return ""
    parts: list[str] = []
    for item in content:
        if not isinstance(item, dict):
            continue
        text = item.get("text")
        if isinstance(text, str) and text.strip():
            parts.append(text)
            continue
        value = item.get("content")
        if isinstance(value, str) and value.strip():
            parts.append(value)
    return collapse_whitespace("\n".join(parts))


def extract_first_user_message(rollout_path: str | None) -> str:
    if not rollout_path:
        return ""
    path = normalize_windows_path(rollout_path)
    if not path:
        return ""
    p = Path(path)
    if not p.exists():
        return ""

    candidates: list[str] = []
    try:
        with p.open("r", encoding="utf-8", errors="ignore") as handle:
            for line in handle:
                raw = line.strip()
                if not raw:
                    continue
                try:
                    row = json.loads(raw)
                except Exception:
                    continue

                msg = ""
                payload = row.get("payload")
                if isinstance(payload, dict):
                    role = str(payload.get("role", "")).lower()
                    if role == "user":
                        msg = read_user_text_from_content(payload.get("content"))
                        if not msg and isinstance(payload.get("text"), str):
                            msg = collapse_whitespace(payload.get("text"))
                    elif isinstance(payload.get("text"), str) and row.get("type") == "user_message":
                        msg = collapse_whitespace(payload.get("text"))
                if not msg and row.get("type") == "user_message" and isinstance(row.get("text"), str):
                    msg = collapse_whitespace(row.get("text"))

                if not msg:
                    continue
                candidates.append(msg)
                if not is_wrapper_message(msg):
                    return shorten(msg)
    except Exception:
        return ""

    if candidates:
        return shorten(candidates[0])
    return ""


def backup_file(path: Path, suffix: str) -> Path:
    backup = path.with_name(path.name + suffix)
    shutil.copy2(path, backup)
    return backup


def build_thread_titles_payload(conn: sqlite3.Connection) -> dict[str, object]:
    rows = conn.execute(
        """
        SELECT id,
               COALESCE(NULLIF(TRIM(title), ''), NULLIF(TRIM(first_user_message), ''), 'Previous Chat') AS display_title
        FROM threads
        ORDER BY updated_at DESC
        """
    ).fetchall()

    titles: dict[str, str] = {}
    order: list[str] = []
    for thread_id, display_title in rows:
        clean = shorten(collapse_whitespace(display_title) or "Previous Chat")
        titles[thread_id] = clean
        order.append(thread_id)
    return {"titles": titles, "order": order}


def ensure_global_state(profile: Path, payload: dict[str, object], stamp: str) -> tuple[bool, str]:
    state_path = profile / ".codex-global-state.json"
    if not state_path.exists():
        return False, "missing global state"

    backup_file(state_path, f".bak_repair_local_threads_{stamp}")

    with state_path.open("r", encoding="utf-8") as handle:
        try:
            state = json.load(handle)
        except Exception:
            state = {}
    if not isinstance(state, dict):
        state = {}

    state["thread-titles"] = payload
    state["recent-tasks-filter"] = "recent"
    state["sidebar-view-v2"] = "threads"
    state["sidebar-workspace-filter-v2"] = "all"
    state["thread-sort-key"] = "updated_at"
    state["stage-filter"] = "all"

    nested = state.get("electron-persisted-atom-state")
    if not isinstance(nested, dict):
        nested = {}
    nested["thread-titles"] = payload

    # Force known-good sidebar filters to avoid cloud-only or narrowed views.
    nested["recent-tasks-filter"] = "recent"
    nested["sidebar-view-v2"] = "threads"
    nested["sidebar-workspace-filter-v2"] = "all"
    nested["thread-sort-key"] = "updated_at"
    nested["stage-filter"] = "all"

    for target in (state, nested):
        target["electron-saved-workspace-roots"] = normalize_root_list(
            target.get("electron-saved-workspace-roots") or []
        )
        target["active-workspace-roots"] = normalize_root_list(target.get("active-workspace-roots") or [])
        target["electron-workspace-root-labels"] = normalize_root_labels(
            target.get("electron-workspace-root-labels") or {}
        )

    state["electron-persisted-atom-state"] = nested

    with state_path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(state, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    return True, "updated"


def repair_profile(profile: Path) -> dict[str, object]:
    out: dict[str, object] = {"profile": str(profile), "status": "skipped"}
    db = profile / "state_5.sqlite"
    if not db.exists():
        out["reason"] = "missing state_5.sqlite"
        return out

    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = backup_file(db, f".bak_repair_local_threads_{stamp}")

    conn = sqlite3.connect(str(db), timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 5000")

    try:
        before_unprefixed = conn.execute(
            "SELECT count(*) FROM threads WHERE cwd GLOB '[A-Za-z]:\\\\*'",
        ).fetchone()[0]
        before_empty = conn.execute(
            """
            SELECT count(*) FROM threads
            WHERE archived = 0 AND (first_user_message IS NULL OR TRIM(first_user_message) = '')
            """
        ).fetchone()[0]

        conn.execute("BEGIN")
        # Normalize every non-null cwd value to avoid exact-match misses in thread/list cwd filter.
        rows_cwd = conn.execute("SELECT id, cwd FROM threads WHERE cwd IS NOT NULL").fetchall()
        for row in rows_cwd:
            thread_id = row["id"]
            current_cwd = row["cwd"]
            normalized_cwd = normalize_cwd_value(current_cwd)
            if normalized_cwd != current_cwd:
                conn.execute("UPDATE threads SET cwd = ? WHERE id = ?", (normalized_cwd, thread_id))

        rows = conn.execute(
            """
            SELECT id, title, rollout_path
            FROM threads
            WHERE archived = 0 AND (first_user_message IS NULL OR TRIM(first_user_message) = '')
            """
        ).fetchall()

        updated_messages = 0
        updated_titles = 0
        for row in rows:
            thread_id = row["id"]
            title = collapse_whitespace(row["title"])
            derived = extract_first_user_message(row["rollout_path"])
            first_message = shorten(title or derived or "Previous Chat")
            if not first_message:
                first_message = "Previous Chat"
            title_for_update = title or first_message

            conn.execute(
                """
                UPDATE threads
                SET first_user_message = ?,
                    title = CASE WHEN title IS NULL OR TRIM(title) = '' THEN ? ELSE title END
                WHERE id = ?
                """,
                (first_message, title_for_update, thread_id),
            )
            updated_messages += 1
            if not title:
                updated_titles += 1

        conn.commit()

        after_unprefixed = conn.execute(
            "SELECT count(*) FROM threads WHERE cwd GLOB '[A-Za-z]:\\\\*'",
        ).fetchone()[0]
        after_empty = conn.execute(
            """
            SELECT count(*) FROM threads
            WHERE archived = 0 AND (first_user_message IS NULL OR TRIM(first_user_message) = '')
            """
        ).fetchone()[0]

        payload = build_thread_titles_payload(conn)
        gs_ok, gs_msg = ensure_global_state(profile, payload, stamp)

        out.update(
            {
                "status": "ok",
                "db_backup": str(backup),
                "cwd_unprefixed_before": before_unprefixed,
                "cwd_unprefixed_after": after_unprefixed,
                "fum_empty_before": before_empty,
                "fum_empty_after": after_empty,
                "fum_rows_updated": updated_messages,
                "empty_titles_filled": updated_titles,
                "global_state": gs_msg if gs_ok else gs_msg,
                "thread_titles_count": len(payload["order"]),
            }
        )
    except Exception as exc:
        conn.rollback()
        out.update({"status": "error", "error": str(exc), "db_backup": str(backup)})
    finally:
        conn.close()
    return out


def main() -> None:
    results = [repair_profile(profile) for profile in PROFILES]
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
