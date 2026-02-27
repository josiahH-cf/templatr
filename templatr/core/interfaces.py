"""Protocol interfaces for core Templatr components.

These Protocol classes define the public contracts for ConfigManager,
TemplateManager, LLMClient, and LLMServerManager. They serve as living
documentation and enable type-checked dependency injection without
requiring concrete classes to inherit from them.

Zero runtime cost — used for type checking and isinstance() verification
via @runtime_checkable.
"""

from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple, runtime_checkable

from typing import Protocol


@runtime_checkable
class ConfigManagerProtocol(Protocol):
    """Protocol for configuration management.

    Public contract:
        config (property): Current Config object, loaded lazily.
        load() -> Config: Load configuration from file.
        save(config=None) -> bool: Save configuration to file.
        update(**kwargs) -> bool: Update specific config values and save.
    """

    @property
    def config(self): ...

    def load(self): ...

    def save(self, config=None) -> bool: ...

    def update(self, **kwargs) -> bool: ...


@runtime_checkable
class TemplateManagerProtocol(Protocol):
    """Protocol for template CRUD operations.

    Public contract:
        list_all() -> List[Template]: List all templates sorted by name.
        load(path) -> Optional[Template]: Load a template from a JSON file.
        get(name) -> Optional[Template]: Get a template by name.
        save(template) -> bool: Save a template to disk.
        delete(template) -> bool: Delete a template from disk.
        create(name, content, ...) -> Template: Create and save a new template.
        list_folders() -> List[str]: List all category folders.
        create_folder(name) -> bool: Create a new category folder.
        delete_folder(name) -> tuple[bool, str]: Delete an empty category folder.
        get_template_folder(template) -> str: Get the folder name for a template.
        save_to_folder(template, folder) -> bool: Save a template to a folder.
        create_version(template, note) -> Optional[TemplateVersion]: Create version snapshot.
        list_versions(template) -> List[TemplateVersion]: List all versions.
        get_version(template, version_num) -> Optional[TemplateVersion]: Get specific version.
        restore_version(template, version_num, create_backup) -> Optional[Template]: Restore version.
    """

    def list_all(self) -> list: ...

    def load(self, path: Path): ...

    def get(self, name: str): ...

    def save(self, template) -> bool: ...

    def delete(self, template) -> bool: ...

    def create(
        self,
        name: str,
        content: str,
        description: str = "",
        trigger: str = "",
        variables: Optional[List[Dict[str, Any]]] = None,
    ): ...

    def list_folders(self) -> List[str]: ...

    def create_folder(self, name: str) -> bool: ...

    def delete_folder(self, name: str) -> Tuple[bool, str]: ...

    def get_template_folder(self, template) -> str: ...

    def save_to_folder(self, template, folder: str = "") -> bool: ...

    def create_version(self, template, note: str = ""): ...

    def list_versions(self, template) -> list: ...

    def get_version(self, template, version_num: int): ...

    def restore_version(self, template, version_num: int, create_backup: bool = True): ...


@runtime_checkable
class LLMClientProtocol(Protocol):
    """Protocol for LLM HTTP client.

    Public contract:
        health_check() -> bool: Check if the server is healthy.
        generate(prompt, ...) -> str: Generate a completion.
        generate_stream(prompt, ...) -> Iterator[str]: Generate with streaming.
    """

    def health_check(self) -> bool: ...

    def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        stream: bool = False,
    ) -> str: ...

    def generate_stream(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> Iterator[str]: ...


@runtime_checkable
class LLMServerProtocol(Protocol):
    """Protocol for LLM server lifecycle management.

    Public contract:
        find_server_binary() -> Optional[Path]: Find the llama-server binary.
        find_models(model_dir=None) -> list[ModelInfo]: Find available model files.
        is_running() -> bool: Check if the server is running.
        start(model_path=None) -> Tuple[bool, str]: Start the server.
        stop() -> Tuple[bool, str]: Stop the server.
    """

    def find_server_binary(self) -> Optional[Path]: ...

    def find_models(self, model_dir: Optional[str] = None) -> list: ...

    def is_running(self) -> bool: ...

    def start(self, model_path: Optional[str] = None) -> Tuple[bool, str]: ...

    def stop(self) -> Tuple[bool, str]: ...
