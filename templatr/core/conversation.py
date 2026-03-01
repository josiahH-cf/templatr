"""Conversation memory for multi-turn chat.

Stores prior user/assistant exchange pairs and assembles them into a single
plain-string prompt compatible with llama.cpp's /completion endpoint.

Format: ChatML role tags (<|im_start|> / <|im_end|>) so chat-tuned models
can distinguish speaker roles.  The assembled string is always a plain text
prompt — no JSON or OpenAI-style messages arrays involved.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import NamedTuple


class _Turn(NamedTuple):
    """A single completed conversation exchange."""

    user: str
    assistant: str


@dataclass
class ConversationMemory:
    """Session-only conversation memory for multi-turn chat.

    Stores completed user/assistant turn pairs and assembles them into a
    ChatML-formatted prompt for the next generation request.

    The memory is intentionally NOT persisted across app restarts —
    existing prompt history handles that separately.

    Attributes:
        max_turns: Maximum number of prior pairs to include.  0 = single-shot.
        context_char_limit: Maximum total characters of the assembled prompt
            (including the new message).  Oldest turns are silently dropped
            when the limit would be exceeded.
    """

    max_turns: int = 6
    context_char_limit: int = 4000

    def __post_init__(self) -> None:
        """Initialise the internal turn list."""
        self._turns: list[_Turn] = []

    def add_turn(self, user_msg: str, assistant_msg: str) -> None:
        """Record a completed exchange.

        Call this after the model finishes generating a response so the
        exchange can be included in the next assembled prompt.

        Args:
            user_msg: The user's message for this turn.
            assistant_msg: The model's reply for this turn.
        """
        self._turns.append(_Turn(user=user_msg, assistant=assistant_msg))

    def assemble_prompt(self, new_user_msg: str) -> tuple[str, bool]:
        """Build a ChatML-formatted prompt that includes prior context.

        Prior turns are included in order from oldest to newest, subject to
        ``max_turns`` and ``context_char_limit``.  When the assembled string
        would exceed the character limit, oldest turns are dropped until it
        fits.

        Args:
            new_user_msg: The latest user message to append.

        Returns:
            A (prompt_string, was_truncated) tuple.
            ``was_truncated`` is True when at least one turn was dropped
            due to the character limit.
        """
        if self.max_turns == 0:
            return new_user_msg, False

        # Apply max_turns cap — keep only the most recent pairs
        candidates = list(self._turns[-self.max_turns :])

        # Short-circuit: no prior turns to include — send raw, preserving
        # pre-feature behaviour for single-shot and non-chat-tuned models.
        if not candidates:
            return new_user_msg, False

        # Build the tail: the closing user turn + assistant prompt
        tail = (
            f"<|im_start|>user\n{new_user_msg}<|im_end|>\n"
            "<|im_start|>assistant\n"
        )

        # Drop oldest turns until the full assembled string fits the limit
        truncated = False
        while candidates:
            prior_parts = [
                f"<|im_start|>user\n{t.user}<|im_end|>\n"
                f"<|im_start|>assistant\n{t.assistant}<|im_end|>\n"
                for t in candidates
            ]
            assembled = "".join(prior_parts) + tail
            if len(assembled) <= self.context_char_limit:
                break
            candidates.pop(0)
            truncated = True
        else:
            # All prior turns dropped by char limit — send raw to avoid
            # emitting a lone, context-free ChatML tail.
            return new_user_msg, truncated

        return assembled, truncated

    def reset(self) -> None:
        """Clear all stored turns.

        Called when the user clears the chat thread or switches templates.
        """
        self._turns.clear()
