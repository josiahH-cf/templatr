# Feature: Multi-Turn Chat (Conversation Memory)

## Description

Every prompt sent to the model is currently stateless — the model has no memory of prior exchanges within a session. Users who want to refine a prompt iteratively or ask follow-up questions must copy-paste previous outputs back into their next message. This feature introduces conversation memory so that sequential messages in the same chat thread build on each other naturally.

## Acceptance Criteria

- [x] AC-1: When the user sends a second message in the same chat thread, the generation request includes prior user/assistant turn(s) as preceding context.
- [x] AC-2: A configurable maximum turn count controls how many prior exchanges are included (default: 6 turns — 3 user + 3 assistant). Setting it to 0 restores single-shot behavior.
- [x] AC-3: The context is formatted so the model can distinguish speaker roles (compatible with llama.cpp's `/completion` endpoint).
- [x] AC-4: Clearing the chat thread (via the existing clear shortcut or `/clear`) also resets conversation memory.
- [x] AC-5: Switching to a different template resets conversation memory.
- [x] AC-6: The `/compare` command sends the full multi-turn context (not just the latest message) so comparisons reflect the conversation.
- [x] AC-7: If the assembled context exceeds a configurable character limit (default: 4000), the oldest turns are silently dropped and the user is notified via a system message.
- [x] AC-8: The prompt recorded in history is the full assembled context so history search remains useful.
- [x] AC-9: Both new settings (turn count, character limit) are accessible through the existing LLM settings dialog — no new UI surface.
- [x] AC-10: README and `/help` output are updated to document multi-turn behavior and the new settings.

## Constraints

- The assembled prompt must be a plain string (llama.cpp `/completion` expects this, not an OpenAI-style messages array).
- No new dependencies.
- Backward compatible: existing config files without the new fields use sensible defaults.
- Conversation memory is session-only — not persisted across app restarts. History persistence is already handled separately.
- Must not break streaming generation.
- **UI principle:** No new buttons, menus, or toolbar items. The settings belong in the existing LLM settings dialog as optional fields. The chat UI behavior changes transparently — the user just keeps typing.

## Out of Scope

- Persisting conversation threads across app sessions (future: session save/restore).
- System prompt injection (templates already provide system context).
- Token-level context management (character count is a sufficient proxy without adding a tokenizer dependency).
- Per-model context isolation during `/compare`.

## Dependencies

- All v1.1 features (complete).

## Notes

- Most GGUF chat-tuned models expect ChatML-style role tags. The implementer should verify the format works with common models and consider making it configurable if needed.
- The turn count is in *turns* (one turn = one user + one assistant pair), not individual messages.
- The 4000-character default is conservative (~1000 tokens for English text), appropriate for small-context models.
