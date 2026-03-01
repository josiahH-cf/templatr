# Prompt A/B Testing

Not sure how consistent the model is on a given prompt? Run it multiple times
with `/test` and compare results side-by-side.

---

## Basic Usage

```
/test             # run the last prompt 3 times (default)
/test 5           # run it 5 times
/test 5 | write a haiku about autumn   # 5 runs with a custom prompt
```

The minimum is 2 iterations.  After all iterations complete, a summary appears
in the chat thread showing latency and estimated token counts for each run.

---

## Picking a Winner

After a test run, type `/test view` to open the detail dialog.  Each iteration's
full output is displayed; click **Pick as Winner ★** to mark that output as a
favourite in your prompt history.

---

## How It Interacts with Conversation Memory

If you pass a custom prompt after `|`, it is assembled with the current
conversation context just like a normal message.  Otherwise, the last
fully-assembled prompt is replayed — this is the same prompt the model actually
saw, including any multi-turn context.
