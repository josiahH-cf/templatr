"""Local LLM integration for Automatr.

Manages the llama.cpp server process and provides an HTTP client
for sending prompts.
"""

import os
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional, Tuple

import requests

from automatr.core.config import get_config


@dataclass
class ModelInfo:
    """Information about a local model file."""

    path: Path
    name: str
    size_gb: float

    @classmethod
    def from_path(cls, path: Path) -> "ModelInfo":
        """Create ModelInfo from a file path."""
        size_bytes = path.stat().st_size
        size_gb = size_bytes / (1024 ** 3)
        return cls(
            path=path,
            name=path.stem,
            size_gb=round(size_gb, 2),
        )


class LLMClient:
    """HTTP client for communicating with llama-server."""

    def __init__(self, base_url: str = "http://localhost:8080"):
        """Initialize the client.

        Args:
            base_url: Base URL of the llama-server.
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = 120  # 2 minutes for generation

    def health_check(self) -> bool:
        """Check if the server is healthy.

        Returns:
            True if server is responding, False otherwise.
        """
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def wait_for_readiness(
        self,
        max_attempts: int = 3,
        delay_seconds: float = 3.0,
        on_retry: Optional[callable] = None,
    ) -> Tuple[bool, str]:
        """Wait for the server to become ready with retries.

        Args:
            max_attempts: Number of attempts before giving up.
            delay_seconds: Seconds to wait between attempts.
            on_retry: Optional callback(attempt, max_attempts) called before each retry.

        Returns:
            Tuple of (ready, error_message). If ready, error_message is empty.
        """
        for attempt in range(1, max_attempts + 1):
            if self.health_check():
                return True, ""

            if attempt < max_attempts:
                if on_retry:
                    on_retry(attempt, max_attempts)
                time.sleep(delay_seconds)

        return False, f"Server not ready after {max_attempts} attempts"

    def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        stream: bool = False,
    ) -> str:
        """Generate a completion for the given prompt.

        Args:
            prompt: The input prompt.
            max_tokens: Maximum tokens to generate. Uses config if None.
            temperature: Sampling temperature. Uses config if None.
            stream: Whether to stream the response.

        Returns:
            Generated text.

        Raises:
            ConnectionError: If server is not reachable.
            RuntimeError: If generation fails.
        """
        # Read settings from config (allows live tuning)
        config = get_config().llm
        payload = {
            "prompt": prompt,
            "n_predict": max_tokens if max_tokens is not None else config.max_tokens,
            "temperature": temperature if temperature is not None else config.temperature,
            "top_p": config.top_p,
            "top_k": config.top_k,
            "repeat_penalty": config.repeat_penalty,
            "stream": stream,
        }

        try:
            response = requests.post(
                f"{self.base_url}/completion",
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()

            data = response.json()
            return data.get("content", "")

        except requests.ConnectionError:
            raise ConnectionError(
                f"Cannot connect to LLM server at {self.base_url}.\n\n"
                "Use LLM → Start Server to start it."
            )
        except requests.Timeout:
            raise RuntimeError(
                "Request timed out.\n\n"
                "The model may be loading or the prompt is too long. Try again."
            )
        except requests.RequestException as e:
            raise RuntimeError(f"Generation failed: {e}")

    def generate_stream(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> Iterator[str]:
        """Generate a completion with streaming.

        Args:
            prompt: The input prompt.
            max_tokens: Maximum tokens to generate. Uses config if None.
            temperature: Sampling temperature. Uses config if None.

        Yields:
            Generated text tokens.
        """
        # Read settings from config (allows live tuning)
        config = get_config().llm
        payload = {
            "prompt": prompt,
            "n_predict": max_tokens if max_tokens is not None else config.max_tokens,
            "temperature": temperature if temperature is not None else config.temperature,
            "top_p": config.top_p,
            "top_k": config.top_k,
            "repeat_penalty": config.repeat_penalty,
            "stream": True,
        }

        try:
            with requests.post(
                f"{self.base_url}/completion",
                json=payload,
                stream=True,
                timeout=self.timeout,
            ) as response:
                response.raise_for_status()

                for line in response.iter_lines():
                    if line:
                        # Parse SSE format
                        line_str = line.decode("utf-8")
                        if line_str.startswith("data: "):
                            import json
                            try:
                                data = json.loads(line_str[6:])
                                content = data.get("content", "")
                                if content:
                                    yield content
                            except json.JSONDecodeError:
                                continue

        except requests.RequestException as e:
            raise RuntimeError(f"Streaming failed: {e}")


class LLMServerManager:
    """Manages the llama-server process lifecycle."""

    def __init__(self):
        """Initialize the server manager."""
        self.config = get_config().llm
        self._process: Optional[subprocess.Popen] = None

    def find_server_binary(self) -> Optional[Path]:
        """Find the llama-server binary.

        Searches in order:
        1. Configured path (config.llm.server_binary)
        2. Automatr data directory (~/.local/share/automatr/llama.cpp/build/bin/)
        3. PATH environment
        4. Legacy locations (~/llama.cpp/build/bin/)

        Returns:
            Path to binary, or None if not found.
        """
        binary_name = "llama-server" if os.name != "nt" else "llama-server.exe"

        # 1. Check configured path
        if self.config.server_binary:
            path = Path(self.config.server_binary).expanduser()
            if path.exists() and os.access(path, os.X_OK):
                return path

        # 2. Check Automatr standard data directory (Linux/WSL)
        automatr_llama = (
            Path.home() / ".local" / "share" / "automatr" / "llama.cpp" / "build" / "bin" / binary_name
        )
        if automatr_llama.exists() and os.access(automatr_llama, os.X_OK):
            return automatr_llama

        # 2b. Check macOS data directory
        automatr_llama_macos = (
            Path.home() / "Library" / "Application Support" / "automatr" / "llama.cpp" / "build" / "bin" / binary_name
        )
        if automatr_llama_macos.exists() and os.access(automatr_llama_macos, os.X_OK):
            return automatr_llama_macos

        # 3. Check PATH
        path_binary = shutil.which(binary_name)
        if path_binary:
            return Path(path_binary)

        # 4. Check legacy/common locations
        candidates = [
            Path.home() / "llama.cpp" / "build" / "bin" / binary_name,
            Path.home() / ".local" / "bin" / binary_name,
            Path("/usr/local/bin") / binary_name,
            Path("/opt/homebrew/bin") / binary_name,  # macOS Apple Silicon
        ]

        for path in candidates:
            if path.exists() and os.access(path, os.X_OK):
                return path

        return None

    def find_models(self, model_dir: Optional[str] = None) -> list[ModelInfo]:
        """Find available model files.

        Args:
            model_dir: Directory to search. Uses config if None.

        Returns:
            List of ModelInfo objects.
        """
        search_dir = model_dir or self.config.model_dir
        if not search_dir:
            search_dir = str(Path.home() / "models")

        path = Path(search_dir).expanduser()
        if not path.exists():
            return []

        models = []
        for file in path.rglob("*.gguf"):
            try:
                models.append(ModelInfo.from_path(file))
            except Exception:
                continue

        return sorted(models, key=lambda m: m.name.lower())

    def get_models_dir(self) -> Path:
        """Get the models directory path.

        Returns:
            Path to the models directory (creates if needed).
        """
        model_dir = self.config.model_dir
        if not model_dir:
            model_dir = str(Path.home() / "models")

        path = Path(model_dir).expanduser()
        path.mkdir(parents=True, exist_ok=True)
        return path

    def import_model(self, source_path: Path) -> Tuple[bool, str]:
        """Import a GGUF model file into the models directory.

        Copies the file to the models directory. Does not overwrite existing files.

        Args:
            source_path: Path to the source GGUF file.

        Returns:
            Tuple of (success, message or destination path).
        """
        if not source_path.exists():
            return False, f"Source file not found: {source_path}"

        if source_path.suffix.lower() != ".gguf":
            return False, "Only .gguf files are supported"

        dest_dir = self.get_models_dir()
        dest_path = dest_dir / source_path.name

        if dest_path.exists():
            return False, f"A model with this name already exists:\n{dest_path}"

        try:
            shutil.copy2(source_path, dest_path)
            return True, str(dest_path)
        except PermissionError:
            return False, f"Permission denied writing to:\n{dest_dir}"
        except OSError as e:
            return False, f"Failed to copy file: {e}"

    def is_running(self) -> bool:
        """Check if the server is currently running.

        Returns:
            True if server is running, False otherwise.
        """
        # Check our process handle
        if self._process:
            if self._process.poll() is None:
                return True
            self._process = None

        # Check by trying to connect
        client = LLMClient(f"http://localhost:{self.config.server_port}")
        return client.health_check()

    def start(self, model_path: Optional[str] = None) -> Tuple[bool, str]:
        """Start the llama-server.

        Args:
            model_path: Path to model file. Uses config if None.

        Returns:
            Tuple of (success, message).
        """
        if self.is_running():
            return True, "Server already running"

        # Find binary
        binary = self.find_server_binary()
        if not binary:
            return False, (
                "llama-server binary not found.\n\n"
                "To fix:\n"
                "1. Run ./install.sh to build llama.cpp, or\n"
                "2. Set 'server_binary' in ~/.config/automatr/config.json"
            )

        # Determine model
        model = model_path or self.config.model_path
        if not model:
            return False, (
                "No model configured.\n\n"
                "To fix:\n"
                "1. Place .gguf model files in ~/models/\n"
                "2. Use LLM → Select Model in the menu, or\n"
                "3. Set 'model_path' in ~/.config/automatr/config.json"
            )

        model_file = Path(model).expanduser()
        if not model_file.exists():
            return False, (
                f"Model file not found:\n{model_file}\n\n"
                "Use LLM → Select Model to choose an available model."
            )

        # Build command
        cmd = [
            str(binary),
            "--model", str(model_file),
            "--port", str(self.config.server_port),
            "--ctx-size", str(self.config.context_size),
        ]

        if self.config.gpu_layers > 0:
            cmd.extend(["--n-gpu-layers", str(self.config.gpu_layers)])

        try:
            # Start process
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True,
            )

            # Wait for server to be ready
            for _ in range(60):  # 30 seconds timeout
                time.sleep(0.5)

                # Check if process died
                if self._process.poll() is not None:
                    _, stderr = self._process.communicate()
                    error = stderr.decode() if stderr else "Unknown error"
                    return False, f"Server failed to start: {error[:200]}"

                # Check if responding
                if self.is_running():
                    return True, "Server started successfully"

            return True, "Server starting (may take a moment to be ready)"

        except Exception as e:
            return False, f"Failed to start server: {e}"

    def stop(self) -> Tuple[bool, str]:
        """Stop the llama-server.

        Returns:
            Tuple of (success, message).
        """
        if not self.is_running():
            return True, "Server not running"

        if self._process:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
            self._process = None
            return True, "Server stopped"

        # Try to find and kill by port or process name
        try:
            import psutil
            for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                try:
                    # Check process name first (most reliable)
                    name = proc.info.get("name", "")
                    if name and "llama-server" in name:
                        proc.terminate()
                        try:
                            proc.wait(timeout=5)
                        except psutil.TimeoutExpired:
                            proc.kill()
                        return True, "Server stopped"

                    # Fallback: check command line
                    cmdline = proc.info.get("cmdline", [])
                    if cmdline and any("llama-server" in arg for arg in cmdline):
                        proc.terminate()
                        try:
                            proc.wait(timeout=5)
                        except psutil.TimeoutExpired:
                            proc.kill()
                        return True, "Server stopped"
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except ImportError:
            # Fallback: try pkill
            result = subprocess.run(["pkill", "-f", "llama-server"], capture_output=True)
            if result.returncode == 0:
                return True, "Server stopped"

        return False, "Could not stop server"


# Global instances
_llm_client: Optional[LLMClient] = None
_llm_server: Optional[LLMServerManager] = None


def get_llm_client() -> LLMClient:
    """Get the global LLM client."""
    global _llm_client
    if _llm_client is None:
        config = get_config().llm
        _llm_client = LLMClient(f"http://localhost:{config.server_port}")
    return _llm_client


def get_llm_server() -> LLMServerManager:
    """Get the global LLM server manager."""
    global _llm_server
    if _llm_server is None:
        _llm_server = LLMServerManager()
    return _llm_server
