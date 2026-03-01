# Multi-Turn Chat

Templatr remembers prior exchanges within a session so you can ask follow-up
questions and refine outputs naturally — no copy-pasting required.

---

## How It Works

Every message you send automatically includes recent user/assistant turns as
context.  The model sees the conversation history, so you can say things like
"make that shorter" or "now write a Python example" and the model understands
what *that* refers to.

---

## Resetting the Conversation

Two things reset the context and start a clean slate:

- Press **Ctrl+L** or use the `/clear` keyboard shortcut.
- Select a different template from the slash palette or sidebar.

---

## Settings

Open `/settings` and adjust under **Generation Settings**:

| Setting | Default | Description |
|---------|---------|-------------|
| Conversation Turns | 6 | Number of prior user/assistant pairs included. Set to **0** to disable memory entirely (single-shot mode). |
| Context Char Limit | 4000 | Maximum characters of assembled context per request. Oldest turns are silently dropped when the limit is hit — a notice appears in the chat. |
