"""Prompt history persistence for generated outputs.

Stores generated prompt/output pairs with per-template filtering,
favorite flags, and simple search by text/date.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from uuid import uuid4

from templatr.core.config import get_data_dir


@dataclass
class PromptHistoryEntry:
    """Single prompt history record."""

    id: str
    template_name: str
    prompt: str
    output: str
    created_at: str
    favorite: bool = False

    def to_dict(self) -> dict:
        """Convert the history entry to a JSON-serializable dictionary."""
        return {
            "id": self.id,
            "template_name": self.template_name,
            "prompt": self.prompt,
            "output": self.output,
            "created_at": self.created_at,
            "favorite": self.favorite,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PromptHistoryEntry":
        """Create a PromptHistoryEntry from persisted dictionary data."""
        return cls(
            id=str(data.get("id", "")),
            template_name=str(data.get("template_name", "")),
            prompt=str(data.get("prompt", "")),
            output=str(data.get("output", "")),
            created_at=str(data.get("created_at", "")),
            favorite=bool(data.get("favorite", False)),
        )


class PromptHistoryStore:
    """File-backed prompt history store."""

    def __init__(
        self,
        file_path: Optional[Path] = None,
        max_entries_per_template: int = 200,
    ) -> None:
        """Initialize a prompt history store.

        Args:
            file_path: Optional explicit path for persistence file.
            max_entries_per_template: Maximum entries retained per template.
        """
        self._file_path = file_path or (get_data_dir() / "prompt_history.json")
        self._max_entries_per_template = max_entries_per_template

    def add_entry(
        self,
        template_name: Optional[str],
        prompt: str,
        output: str,
        created_at: Optional[str] = None,
    ) -> PromptHistoryEntry:
        """Append a new history entry and persist it.

        Args:
            template_name: Template name associated with output, if any.
            prompt: Rendered prompt sent to the model.
            output: Final model output.
            created_at: Optional ISO timestamp override for tests.

        Returns:
            The created PromptHistoryEntry.
        """
        normalized_template = (template_name or "__plain__").strip() or "__plain__"
        timestamp = created_at or _utc_now_iso()

        entry = PromptHistoryEntry(
            id=uuid4().hex,
            template_name=normalized_template,
            prompt=prompt,
            output=output,
            created_at=timestamp,
            favorite=False,
        )

        entries = self._read_entries()
        entries.append(entry)
        entries = self._trim_entries(entries)
        self._write_entries(entries)
        return entry

    def list_entries(
        self,
        template_name: Optional[str] = None,
        query: Optional[str] = None,
        date_prefix: Optional[str] = None,
        favorites_only: bool = False,
        limit: Optional[int] = 20,
    ) -> list[PromptHistoryEntry]:
        """List entries with optional filters.

        Args:
            template_name: Restrict to this template name.
            query: Case-insensitive text search over prompt and output.
            date_prefix: Date filter using ISO prefix, e.g. ``YYYY-MM-DD``.
            favorites_only: Restrict to entries marked favorite.
            limit: Maximum number of records to return. ``None`` means no limit.

        Returns:
            Filtered entries in reverse-chronological order.
        """
        entries = self._read_entries()

        if template_name:
            entries = [e for e in entries if e.template_name == template_name]
        if favorites_only:
            entries = [e for e in entries if e.favorite]
        if query:
            query_lc = query.lower()
            entries = [
                e
                for e in entries
                if query_lc in e.prompt.lower() or query_lc in e.output.lower()
            ]
        if date_prefix:
            entries = [e for e in entries if e.created_at.startswith(date_prefix)]

        entries.sort(key=lambda e: e.created_at, reverse=True)
        if limit is not None:
            entries = entries[:limit]
        return entries

    def mark_favorite(self, entry_id: str, favorite: bool = True) -> bool:
        """Set favorite status for an entry by id.

        Args:
            entry_id: Target entry id.
            favorite: Desired favorite value.

        Returns:
            True when an entry was updated, otherwise False.
        """
        entries = self._read_entries()
        updated = False
        for entry in entries:
            if entry.id == entry_id:
                entry.favorite = favorite
                updated = True
                break

        if updated:
            self._write_entries(entries)
        return updated

    def mark_latest_favorite(
        self,
        template_name: Optional[str],
        output: str,
        favorite: bool = True,
    ) -> bool:
        """Set favorite status on the newest entry matching template/output.

        Args:
            template_name: Template name, or ``None`` for plain entries.
            output: Output text to match.
            favorite: Desired favorite state.

        Returns:
            True when an entry was found and updated.
        """
        target_template = (template_name or "__plain__").strip() or "__plain__"
        entries = self._read_entries()
        candidates = [
            entry
            for entry in entries
            if entry.template_name == target_template and entry.output == output
        ]
        if not candidates:
            return False

        candidates.sort(key=lambda e: e.created_at, reverse=True)
        return self.mark_favorite(candidates[0].id, favorite=favorite)

    def _trim_entries(self, entries: list[PromptHistoryEntry]) -> list[PromptHistoryEntry]:
        """Trim history to max entries per template."""
        if self._max_entries_per_template <= 0:
            return entries

        grouped: dict[str, list[PromptHistoryEntry]] = {}
        for entry in entries:
            grouped.setdefault(entry.template_name, []).append(entry)

        trimmed: list[PromptHistoryEntry] = []
        for template_entries in grouped.values():
            template_entries.sort(key=lambda e: e.created_at, reverse=True)
            trimmed.extend(template_entries[: self._max_entries_per_template])

        trimmed.sort(key=lambda e: e.created_at)
        return trimmed

    def _read_entries(self) -> list[PromptHistoryEntry]:
        """Read all entries from disk.

        Invalid files are treated as empty history.
        """
        if not self._file_path.exists():
            return []
        try:
            data = json.loads(self._file_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []

        raw_entries = data.get("entries", []) if isinstance(data, dict) else []
        if not isinstance(raw_entries, list):
            return []
        return [PromptHistoryEntry.from_dict(item) for item in raw_entries if isinstance(item, dict)]

    def _write_entries(self, entries: list[PromptHistoryEntry]) -> None:
        """Persist entries to disk."""
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"entries": [entry.to_dict() for entry in entries]}
        self._file_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


_prompt_history_store_cache: Optional[PromptHistoryStore] = None


def get_prompt_history_store() -> PromptHistoryStore:
    """Return a process-wide prompt history store singleton."""
    global _prompt_history_store_cache
    if _prompt_history_store_cache is None:
        _prompt_history_store_cache = PromptHistoryStore()
    return _prompt_history_store_cache


def _utc_now_iso() -> str:
    """Return the current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
