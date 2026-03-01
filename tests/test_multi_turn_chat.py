"""Tests for multi-turn chat conversation memory (AC-1 through AC-10).

Covers:
- ConversationMemory assembly and truncation logic
- Config fields for max_turns and context_char_limit
- MainWindow integration: clear resets memory, template switch resets memory
- /compare uses assembled multi-turn context
- LLMSettingsDialog exposes the two new fields

These tests were written before the implementation (TDD).
"""

from __future__ import annotations

from templatr.core.conversation import ConversationMemory

# ---------------------------------------------------------------------------
# Unit tests: ConversationMemory
# ---------------------------------------------------------------------------


def test_no_prior_turns_returns_raw_message():
    """AC-1: With no prior turns, assemble returns the exact raw message (not ChatML-wrapped)."""
    mem = ConversationMemory(max_turns=6, context_char_limit=4000)
    prompt, truncated = mem.assemble_prompt("Hello")
    assert prompt == "Hello"
    assert truncated is False


def test_single_prior_turn_included():
    """AC-1: Second message includes the prior user/assistant exchange."""
    mem = ConversationMemory(max_turns=6, context_char_limit=4000)
    mem.add_turn("First question", "First answer")
    prompt, truncated = mem.assemble_prompt("Follow-up")
    assert "First question" in prompt
    assert "First answer" in prompt
    assert "Follow-up" in prompt
    assert truncated is False


def test_speaker_roles_are_distinguishable():
    """AC-3: Assembled prompt uses role markers distinguishable by the model."""
    mem = ConversationMemory(max_turns=6, context_char_limit=4000)
    mem.add_turn("user says this", "assistant says that")
    prompt, _ = mem.assemble_prompt("new message")
    # ChatML role tags must be present
    assert "<|im_start|>user" in prompt
    assert "<|im_start|>assistant" in prompt
    assert "<|im_end|>" in prompt


def test_max_turns_zero_returns_raw_message():
    """AC-2: max_turns=0 produces single-shot behavior — no prior context."""
    mem = ConversationMemory(max_turns=0, context_char_limit=4000)
    mem.add_turn("earlier user", "earlier assistant")
    prompt, truncated = mem.assemble_prompt("new message")
    assert "earlier user" not in prompt
    assert "new message" in prompt
    assert truncated is False


def test_max_turns_limits_included_pairs():
    """AC-2: Only the most recent max_turns pairs are included."""
    mem = ConversationMemory(max_turns=2, context_char_limit=8000)
    mem.add_turn("turn1 user", "turn1 assistant")
    mem.add_turn("turn2 user", "turn2 assistant")
    mem.add_turn("turn3 user", "turn3 assistant")
    prompt, _ = mem.assemble_prompt("new message")
    # turn1 (oldest) should be dropped, turn2 and turn3 should be present
    assert "turn1 user" not in prompt
    assert "turn2 user" in prompt
    assert "turn3 user" in prompt


def test_context_char_limit_drops_oldest_turns():
    """AC-7: When assembled context exceeds the char limit the oldest turns are dropped."""
    # Each turn is ~50 chars; set a tight limit so only the newest fits
    mem = ConversationMemory(max_turns=10, context_char_limit=200)
    mem.add_turn("a" * 60, "b" * 60)
    mem.add_turn("c" * 60, "d" * 60)
    prompt, truncated = mem.assemble_prompt("new message")
    assert truncated is True
    # The first (oldest) turn should have been dropped
    assert "a" * 60 not in prompt


def test_context_char_limit_not_exceeded_no_truncation():
    """AC-7: When context is within the limit truncated is False."""
    mem = ConversationMemory(max_turns=6, context_char_limit=10_000)
    mem.add_turn("short user", "short assistant")
    _, truncated = mem.assemble_prompt("short new")
    assert truncated is False


def test_reset_clears_all_turns():
    """AC-4/AC-5: After reset(), no prior turns appear in assembled output."""
    mem = ConversationMemory(max_turns=6, context_char_limit=4000)
    mem.add_turn("old user", "old assistant")
    mem.reset()
    prompt, _ = mem.assemble_prompt("new message")
    assert "old user" not in prompt
    assert "old assistant" not in prompt


def test_add_turn_after_reset_works_correctly():
    """Turns added after reset appear normally."""
    mem = ConversationMemory(max_turns=6, context_char_limit=4000)
    mem.add_turn("before reset", "ignored")
    mem.reset()
    mem.add_turn("after reset user", "after reset assistant")
    prompt, _ = mem.assemble_prompt("final message")
    assert "before reset" not in prompt
    assert "after reset user" in prompt


# ---------------------------------------------------------------------------
# Config tests
# ---------------------------------------------------------------------------


def test_llm_config_has_max_turns_default():
    """AC-2/AC-9: LLMConfig has max_turns defaulting to 6."""
    from templatr.core.config import LLMConfig

    cfg = LLMConfig()
    assert cfg.max_turns == 6


def test_llm_config_has_context_char_limit_default():
    """AC-7/AC-9: LLMConfig has context_char_limit defaulting to 4000."""
    from templatr.core.config import LLMConfig

    cfg = LLMConfig()
    assert cfg.context_char_limit == 4000


def test_config_from_dict_ignores_missing_new_fields():
    """AC backward-compat: config dicts without the new fields use defaults."""
    from templatr.core.config import LLMConfig, fields

    minimal = {"model_path": "", "max_tokens": 512}
    llm_fields = {f.name for f in fields(LLMConfig)}
    cfg = LLMConfig(**{k: v for k, v in minimal.items() if k in llm_fields})
    assert cfg.max_turns == 6
    assert cfg.context_char_limit == 4000


# ---------------------------------------------------------------------------
# UI integration tests
# ---------------------------------------------------------------------------


def test_clear_chat_resets_conversation_memory(qtbot):
    """AC-4: _clear_chat resets conversation memory on the main window."""
    from unittest.mock import patch

    from templatr.ui.main_window import MainWindow

    with (
        patch("templatr.ui.main_window.get_llm_server"),
        patch("templatr.ui.main_window.get_llm_client"),
        patch("templatr.integrations.llm.LLMServerManager"),
    ):
        window = MainWindow()
        qtbot.addWidget(window)

        # Inject a prior turn
        window.conversation_memory.add_turn("prior user", "prior assistant")
        assert window.conversation_memory._turns  # has data

        window._clear_chat()
        assert not window.conversation_memory._turns  # cleared


def test_template_switch_resets_conversation_memory(qtbot):
    """AC-5: Selecting a different template resets conversation memory."""
    from unittest.mock import patch

    from templatr.core.templates import Template
    from templatr.ui.main_window import MainWindow

    with (
        patch("templatr.ui.main_window.get_llm_server"),
        patch("templatr.ui.main_window.get_llm_client"),
        patch("templatr.integrations.llm.LLMServerManager"),
    ):
        window = MainWindow()
        qtbot.addWidget(window)

        window.conversation_memory.add_turn("prior user", "prior assistant")

        fake_template = Template(
            name="Other Template", content="Do {{thing}}", description="", variables=[]
        )
        window._on_template_selected(fake_template)

        assert not window.conversation_memory._turns


def test_llm_settings_dialog_has_max_turns_field(qtbot):
    """AC-9: LLMSettingsDialog exposes a max_turns spinbox."""
    from templatr.ui.llm_settings import LLMSettingsDialog

    dialog = LLMSettingsDialog()
    qtbot.addWidget(dialog)
    assert hasattr(dialog, "max_turns_spin")


def test_llm_settings_dialog_has_context_char_limit_field(qtbot):
    """AC-9: LLMSettingsDialog exposes a context_char_limit spinbox."""
    from templatr.ui.llm_settings import LLMSettingsDialog

    dialog = LLMSettingsDialog()
    qtbot.addWidget(dialog)
    assert hasattr(dialog, "context_char_limit_spin")


def test_all_turns_dropped_returns_raw_message():
    """When char limit is too tight for even one turn, raw message is returned (no lone ChatML tail)."""
    mem = ConversationMemory(max_turns=6, context_char_limit=50)  # very tight
    mem.add_turn("a" * 40, "b" * 40)  # ~200 chars of ChatML — won't fit
    prompt, truncated = mem.assemble_prompt("short")
    assert prompt == "short"
    assert truncated is True
    assert "<|im_start|>" not in prompt


def test_no_chatm_tags_when_no_prior_turns():
    """ChatML tags are absent when there are no prior turns to include."""
    mem = ConversationMemory(max_turns=6, context_char_limit=4000)
    prompt, _ = mem.assemble_prompt("plain message")
    assert "<|im_start|>" not in prompt
    assert "<|im_end|>" not in prompt


# ---------------------------------------------------------------------------
# AC-6: /compare assembles conversation context
# ---------------------------------------------------------------------------


def test_compare_assembles_context_for_explicit_prompt(qtbot):
    """AC-6: /compare with | explicit prompt wraps it in conversation context."""
    from unittest.mock import MagicMock, patch

    from templatr.ui.main_window import MainWindow

    with (
        patch("templatr.ui.main_window.get_llm_server"),
        patch("templatr.ui.main_window.get_llm_client"),
        patch("templatr.integrations.llm.LLMServerManager"),
    ):
        window = MainWindow()
        qtbot.addWidget(window)

        # Seed a prior turn so conversation context exists
        window.conversation_memory.add_turn("earlier question", "earlier answer")

        # Patch find_models to return 2 fake models so /compare doesn't bail early
        from pathlib import Path

        from templatr.integrations.llm import ModelInfo

        fake_models = [
            ModelInfo(name="model-a", path=Path("/fake/model_a.gguf"), size_gb=0.0),
            ModelInfo(name="model-b", path=Path("/fake/model_b.gguf"), size_gb=0.0),
        ]

        # Capture what prompt MultiModelCompareWorker is started with
        with patch("templatr.ui.main_window.get_llm_server") as mock_server, patch(
            "templatr.ui.main_window.MultiModelCompareWorker"
        ) as mock_worker_cls:
            mock_server.return_value.find_models.return_value = fake_models
            mock_server.return_value.is_running.return_value = True
            mock_instance = MagicMock()
            mock_worker_cls.return_value = mock_instance

            window._handle_compare_command("/compare model-a,model-b | follow-up question")

            assert mock_worker_cls.called
            used_prompt = mock_worker_cls.call_args[0][0]
            # The prompt should contain prior conversation context
            assert "earlier question" in used_prompt
            assert "earlier answer" in used_prompt
            assert "follow-up question" in used_prompt


def test_compare_uses_last_assembled_prompt_when_no_explicit_prompt(qtbot):
    """AC-6: /compare without | uses _last_prompt which is already the assembled context."""
    from unittest.mock import MagicMock, patch

    from templatr.ui.main_window import MainWindow

    with (
        patch("templatr.ui.main_window.get_llm_server"),
        patch("templatr.ui.main_window.get_llm_client"),
        patch("templatr.integrations.llm.LLMServerManager"),
    ):
        window = MainWindow()
        qtbot.addWidget(window)

        # Simulate a prior generation having stored an assembled prompt
        assembled_ctx = "<|im_start|>user\nprev<|im_end|>\n<|im_start|>assistant\nans<|im_end|>\n<|im_start|>user\ncurrent<|im_end|>\n<|im_start|>assistant\n"
        window._last_prompt = assembled_ctx

        from pathlib import Path

        from templatr.integrations.llm import ModelInfo

        fake_models = [
            ModelInfo(name="model-a", path=Path("/fake/model_a.gguf"), size_gb=0.0),
            ModelInfo(name="model-b", path=Path("/fake/model_b.gguf"), size_gb=0.0),
        ]

        with patch("templatr.ui.main_window.get_llm_server") as mock_server, patch(
            "templatr.ui.main_window.MultiModelCompareWorker"
        ) as mock_worker_cls:
            mock_server.return_value.find_models.return_value = fake_models
            mock_server.return_value.is_running.return_value = True
            mock_instance = MagicMock()
            mock_worker_cls.return_value = mock_instance

            window._handle_compare_command("/compare")

            used_prompt = mock_worker_cls.call_args[0][0]
            assert used_prompt == assembled_ctx


# ---------------------------------------------------------------------------
# AC-9: Settings persistence
# ---------------------------------------------------------------------------


def test_llm_settings_saves_max_turns(qtbot, tmp_config_dir, monkeypatch):
    """AC-9: Saving LLMSettingsDialog persists max_turns to config."""
    from templatr.core.config import get_config_manager
    from templatr.ui.llm_settings import LLMSettingsDialog

    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_config_dir))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_config_dir))
    from templatr.core import config as config_mod

    config_mod.reset()

    dialog = LLMSettingsDialog()
    qtbot.addWidget(dialog)
    dialog.max_turns_spin.setValue(3)
    dialog._save_settings()

    loaded = get_config_manager().config
    assert loaded.llm.max_turns == 3
