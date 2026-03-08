### BUG-001: llama.cpp install reports success but runtime is unusable
- **Location:** `templatr/integrations` (llama.cpp install/detection flow)
- **Phase:** 7b Bug Track
- **Severity:** blocking
- **Expected:** Running `./install` results in a usable llama.cpp runtime that the app auto-detects, starts from the toolbar, and can load models.
- **Actual:** Install appears successful but llama.cpp is not reliably installed/detected and runtime use fails.
- **Root cause:** (1) No binary verification after cmake build — output path varies across llama.cpp versions. (2) Smoke test only warned instead of failing. (3) Git clone URL pointed to old repo. (4) No download fallback. (5) vendor/llama-server/ not in runtime search paths.
- **Fix:** install.sh now verifies binary after build, searches alternative output locations, falls back to pre-built download, and smoke test fails on missing binary. config.py adds vendor/llama-server/ to search paths.
- **Fix-as-you-go:** no
- **Status:** fixed
- **Logged:** 2026-03-08
- **Fixed:** 2026-03-08

### BUG-002: generate/chat run hangs after server start
- **Location:** `templatr/ui` (generation/chat execution path)
- **Phase:** 7b Bug Track
- **Severity:** blocking
- **Expected:** After starting server and sending generate/chat requests, the app remains interactive, shows progress/streaming, and returns output.
- **Actual:** After server start and chat entry, UI appears to hang for at least 5 minutes with no usable completion.
- **Root cause:** (1) server.start() blocked the UI thread for up to 30 seconds with time.sleep() loop. (2) Streaming timeout was a single value applied only to initial connection; once the server accepted but slowly loaded a model, iter_lines() blocked indefinitely. (3) Stop button set a flag but couldn't interrupt a blocked iter_lines() call.
- **Fix:** Moved server.start() to ServerStartWorker (QThread). Changed streaming timeout to (10, 90) tuple for separate connect/read limits. Added close_active_stream() to LLMClient so stop() can close the underlying response and unblock iter_lines(). Both llm_toolbar and _generation now use async server start.
- **Fix-as-you-go:** no
- **Status:** fixed
- **Logged:** 2026-03-08
- **Fixed:** 2026-03-08

### BUG-003: template content appears implicitly in chat response
- **Location:** `templatr/ui` + template application flow
- **Phase:** 7b Bug Track
- **Severity:** blocking
- **Expected:** Chat responses should not include implicit template injection unless the user explicitly selected a template.
- **Actual:** Template-like content appears in response output without explicit selection.
- **Fix-as-you-go:** no
- **Status:** open
- **Logged:** 2026-03-08

### BUG-004: output pane is non-scrollable and bulky
- **Location:** `templatr/ui/output_pane.py`
- **Phase:** 7b Bug Track
- **Severity:** blocking
- **Expected:** Output pane supports vertical scrolling and readable wrapping for long returned information in full-window usage.
- **Actual:** Returned information UI is bulky and non-scrollable in the output pane.
- **Fix-as-you-go:** no
- **Status:** open
- **Logged:** 2026-03-08
