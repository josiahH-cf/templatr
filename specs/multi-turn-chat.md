# Feature: Multi-Turn Chat (Conversation Memory)

## Description

Enable multi-turn conversations by maintaining a message history buffer that is prepended to each generation request. Currently, every prompt is sent in isolation — the model has no memory of prior exchanges. This feature adds a sliding-window context that carries previous user/assistant turns, making iterative prompt refinement and follow-up questions natural within a single session.

## Acceptance Criteria

- [ ] AC-1: When the user sends a second message in the same chat thread, the generation request includes the prior user/assistant turn(s) as context preceding the new message.
- [ ] AC-2: A configurable `context_window` setting in `config.json` under `llm` controls the maximum number of prior turns (default: 6 turns, i.e. 3 user + 3 assistant pairs). Setting it to `0` restores single-shot behavior.
- [ ] AC-3: The context buffer is constructed in chat-ML or llama.cpp-compatible format (`<|user|>`, `<|assistant|>` tags or equivalent) so the model can distinguish roles.
- [ ] AC-4: Clearing the chat thread (`Ctrl+L` or `/clear`) also resets the conversation memory buffer, so the next message starts fresh.
- [ ] AC-5: Switching templates resets the conversation memory buffer.
- [ ] AC-6: The `/compare` command uses the assembled multi-turn context (not just the latest message) as its prompt, so comparisons reflect the full conversation.
- [ ] AC-7: If the assembled context exceeds a configurable `max_context_chars` limit (default: 4000), the oldest turns are dropped until it fits, and a system message warns the user that older context was trimmed.
- [ ] AC-8: The prompt recorded in `PromptHistoryStore` is the full assembled context (not just the latest user message), so history search remains useful.

## Affected Areas

### Source files modified
- `templatr/core/config.py` — Add `context_window` (int, default 6) and `max_context_chars` (int, default 4000) fields to `LLMConfig`.
- `templatr/ui/_generation.py` — New `ConversationBuffer` class that tracks turns and assembles the multi-turn prompt. Modify `_generate()` to prepend context from the buffer. Append user/assistant turns after each completed generation.
- `templatr/ui/main_window.py` — Reset the conversation buffer on template switch and on `clear_history()`. Pass buffer to `/compare` flow.
- `templatr/ui/workers.py` — `GenerationWorker.__init__` already accepts `prompt: str`; no change needed if the assembled prompt is passed in.

### New files
- `templatr/core/conversation.py` — `ConversationBuffer` class: `add_user(text)`, `add_assistant(text)`, `assemble(new_user_message) -> str`, `clear()`, `turn_count() -> int`. Handles format, sliding window, and max-chars trimming.
- `tests/test_conversation.py` — Unit tests for buffer assembly, sliding window, trimming, and clear behavior.

### Test files requiring updates
- `tests/test_keyboard_shortcuts.py` — Verify `Ctrl+L` still clears thread (already tested; may need buffer-clear assertion).

## Constraints

- The assembled prompt format must work with llama.cpp's `/completion` endpoint (plain text with role tags, not OpenAI chat format).
- No new dependencies — string assembly only.
- Backward compatible: existing `config.json` files without the new fields use defaults.
- The conversation buffer lives in memory only — not persisted across app restarts. History persistence is already handled by `PromptHistoryStore`.
- Must not break streaming: the full assembled prompt is passed to `GenerationWorker` as a single string, same as today.

## Out of Scope

- Persisting conversation threads across app sessions (future: session save/restore).
- System prompt injection (templates already provide the system context).
- Token-level context management (we use character count as a proxy; true token counting requires a tokenizer dependency).
- Multi-model comparison with per-model context isolation.

## Dependencies

- `chat-ui-core` (complete) — `ChatWidget` displays the message thread.
- `keyboard-shortcuts` (complete) — `Ctrl+L` clear-chat shortcut.

## Notes

- llama.cpp's `/completion` endpoint accepts a flat `prompt` string. The conversation buffer formats turns as:
  ```
  <|user|>
  {user message}
  <|assistant|>
  {assistant response}
  <|user|>
  {new message}
  <|assistant|>
  ```
  This is the ChatML convention that most GGUF chat-tuned models expect.
- The `context_window` count is in *turns* (one turn = one user + one assistant message), not individual messages.
- The `max_context_chars` guard prevents accidentally sending enormous prompts to small-context models. The 4000-character default is conservative (~1000 tokens for English text).
