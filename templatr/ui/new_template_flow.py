"""Conversational /new template quick-create flow.

Implements a simple state machine that collects a template name and content
via successive user inputs, auto-detects ``{{variable}}`` placeholders,
and saves the result through TemplateManager.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional

from templatr.core.templates import (
    Template,
    TemplateManager,
    auto_detect_variables,
)


class _State(Enum):
    """Internal states of the new-template flow."""

    AWAITING_NAME = auto()
    AWAITING_CONTENT = auto()
    DONE = auto()


@dataclass
class FlowResult:
    """Result of a single ``handle_input`` step.

    Attributes:
        message: System message to display in the chat.
        done: True when the flow has finished (success or cancel).
        template: The created Template on success, None otherwise.
        cancelled: True when the user cancelled.
    """

    message: str
    done: bool = False
    template: Optional[Template] = None
    cancelled: bool = False


class NewTemplateFlow:
    """Multi-step conversational flow for creating a template via ``/new``.

    Usage::

        flow = NewTemplateFlow(template_manager)
        messages = flow.start()        # show initial prompt
        result = flow.handle_input(text)  # process each user reply

    The flow moves through AWAITING_NAME → AWAITING_CONTENT → DONE.
    At any point the user can type ``/cancel`` to abort.

    Args:
        manager: TemplateManager used to check conflicts and save.
    """

    def __init__(self, manager: TemplateManager) -> None:
        self._manager = manager
        self._state = _State.AWAITING_NAME
        self._name: str = ""

    @property
    def is_active(self) -> bool:
        """Return True while the flow is still expecting input."""
        return self._state != _State.DONE

    def start(self) -> List[str]:
        """Begin the flow and return the initial system messages.

        Returns:
            A list of system-message strings to display in the chat.
        """
        self._state = _State.AWAITING_NAME
        return ["What should this command be called?"]

    def handle_input(self, text: str) -> FlowResult:
        """Process user input for the current step.

        Args:
            text: Raw user text from the input bar.

        Returns:
            A FlowResult describing the next system message, whether the
            flow is done, and the created Template (if any).
        """
        stripped = text.strip()

        # Global cancel
        if stripped.lower() == "/cancel":
            self._state = _State.DONE
            return FlowResult(
                message="Template creation cancelled.",
                done=True,
                cancelled=True,
            )

        if self._state == _State.AWAITING_NAME:
            return self._handle_name(stripped)
        elif self._state == _State.AWAITING_CONTENT:
            return self._handle_content(stripped)
        else:
            return FlowResult(message="Flow already complete.", done=True)

    # -- Private step handlers -----------------------------------------------

    def _handle_name(self, name: str) -> FlowResult:
        """Validate and store the template name.

        Args:
            name: Candidate template name.
        """
        if not name:
            return FlowResult(
                message="Please provide a non-empty name for the template."
            )

        # Check for conflicts
        existing = self._manager.get(name)
        if existing is not None:
            return FlowResult(
                message=(
                    f"A template named '{name}' already exists. "
                    "Please choose a different name."
                ),
            )

        self._name = name
        self._state = _State.AWAITING_CONTENT
        return FlowResult(
            message=(
                "Paste the prompt content below.\n"
                "Use `{{variable_name}}` for placeholders:"
            ),
        )

    def _handle_content(self, content: str) -> FlowResult:
        """Detect variables, save template, and finish.

        Args:
            content: Raw template content from the user.
        """
        variables = auto_detect_variables(content)
        template = self._manager.create(
            name=self._name,
            content=content,
            variables=[v.to_dict() for v in variables],
        )

        if variables:
            var_names = ", ".join(v.name for v in variables)
            message = f"Found variables: {var_names}. " f"Saved as `/{self._name}`!"
        else:
            message = f"Template saved as `/{self._name}`!"

        self._state = _State.DONE
        return FlowResult(message=message, done=True, template=template)
