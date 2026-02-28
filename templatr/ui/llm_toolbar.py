"""LLM server toolbar widget with server controls and status display."""

from pathlib import Path

from PyQt6.QtCore import Qt, QTimer, QUrl, pyqtSignal
from PyQt6.QtGui import QAction, QDesktopServices
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QWidget,
)

from templatr.core.config import get_config
from templatr.integrations.llm import get_llm_server
from templatr.ui.workers import ModelCopyWorker


class LLMToolbar(QWidget):
    """Toolbar widget for LLM server controls, status display, and model management."""

    status_message = pyqtSignal(str, int)
    server_running_changed = pyqtSignal(bool)

    HEALTH_POLL_INTERVAL_MS = 10_000  # 10 seconds

    def __init__(self, parent=None):
        super().__init__(parent)
        self._model_menu = None
        self._copy_worker = None
        self._progress_dialog = None
        self._was_running = False
        self._setup_ui()

        # Health polling timer - checks server every 10 seconds
        self._health_timer = QTimer(self)
        self._health_timer.timeout.connect(self._poll_health)
        self._health_timer.start(self.HEALTH_POLL_INTERVAL_MS)

    def _setup_ui(self):
        """Build the toolbar layout."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.server_btn = QPushButton("Start Server")
        self.server_btn.setObjectName("secondary")
        self.server_btn.clicked.connect(self.smart_server_action)
        layout.addWidget(self.server_btn)

        self.stop_server_btn = QPushButton("Stop Server")
        self.stop_server_btn.setObjectName("secondary")
        self.stop_server_btn.clicked.connect(self.stop_server)
        self.stop_server_btn.setEnabled(False)
        layout.addWidget(self.stop_server_btn)

        self.llm_status_label = QLabel("LLM: Checking...")
        layout.addWidget(self.llm_status_label)

    def set_model_menu(self, menu):
        """Set the model menu reference for population."""
        self._model_menu = menu
        self._model_menu.aboutToShow.connect(self.populate_model_menu)

    def start_server(self):
        """Start the LLM server."""
        server = get_llm_server()
        if server.is_running():
            self.status_message.emit("Server already running", 3000)
            return

        self.status_message.emit("Starting server...", 0)
        QApplication.processEvents()

        success, message = server.start()
        if success:
            self.status_message.emit("Server started", 3000)
        else:
            QMessageBox.critical(self.window(), "Server Error", message)

        self.check_status()

    def stop_server(self):
        """Stop the LLM server."""
        server = get_llm_server()
        success, message = server.stop()

        if success:
            self.status_message.emit(message, 3000)
        else:
            QMessageBox.warning(self.window(), "Server", message)

        self.check_status()

    def smart_server_action(self):
        """Start server if not running, open browser if running."""
        server = get_llm_server()

        if server.is_running():
            self.launch_web_server()
        else:
            self.status_message.emit("Starting server...", 0)
            QApplication.processEvents()

            success, message = server.start()
            if success:
                self.status_message.emit("Server started", 3000)
            else:
                self.status_message.emit(f"Failed to start server: {message}", 5000)

            self.check_status()

    def launch_web_server(self):
        """Open the LLM web server in the default browser."""
        config = get_config()
        port = config.llm.server_port
        url = QUrl(f"http://127.0.0.1:{port}")
        QDesktopServices.openUrl(url)
        self.status_message.emit(f"Opened http://127.0.0.1:{port} in browser", 3000)

    def check_status(self):
        """Check if the LLM server is running and update UI."""
        server = get_llm_server()
        is_running = server.is_running()

        if is_running:
            self._was_running = True
            self._update_health_status("healthy")
        else:
            self._was_running = False
            self._update_health_status("stopped")

        self.server_running_changed.emit(is_running)

    def _poll_health(self):
        """Poll the server health and update the status label.

        Called periodically by _health_timer. Detects server death by
        checking if a previously-running server has stopped responding.
        """
        server = get_llm_server()
        is_running = server.is_running()

        if is_running:
            # Server is alive — check /health endpoint for detailed status
            from templatr.integrations.llm import LLMClient, get_config

            config = get_config().llm
            client = LLMClient(f"http://localhost:{config.server_port}")
            try:
                import requests

                resp = requests.get(f"{client.base_url}/health", timeout=5)
                if resp.status_code == 200:
                    self._update_health_status("healthy")
                else:
                    self._update_health_status("degraded")
            except Exception:
                self._update_health_status("degraded")
            self._was_running = True
        else:
            if self._was_running:
                # Server was running but now isn't — unexpected death
                self._update_health_status("stopped")
                self.status_message.emit(
                    "LLM server stopped unexpectedly. "
                    "Use LLM → Start Server to restart.",
                    10000,
                )
                self._was_running = False
            else:
                self._update_health_status("stopped")

        self.server_running_changed.emit(is_running)

    def _update_health_status(self, status: str):
        """Update the toolbar status label to reflect server health.

        Args:
            status: One of "healthy", "degraded", or "stopped".
        """
        if status == "healthy":
            self.llm_status_label.setText("LLM: Healthy")
            self.llm_status_label.setStyleSheet("color: #4ec9b0;")
            self.server_btn.setText("Open Server")
            self.server_btn.setStyleSheet("background-color: #4ec9b0; color: #1e1e1e;")
            self.stop_server_btn.setEnabled(True)
            self.stop_server_btn.setStyleSheet(
                "background-color: #c42b1c; color: #ffffff;"
            )
        elif status == "degraded":
            self.llm_status_label.setText("LLM: Degraded")
            self.llm_status_label.setStyleSheet("color: #c9a04e;")
            self.server_btn.setText("Open Server")
            self.server_btn.setStyleSheet("")
            self.stop_server_btn.setEnabled(True)
            self.stop_server_btn.setStyleSheet(
                "background-color: #c42b1c; color: #ffffff;"
            )
        else:  # stopped
            self.llm_status_label.setText("LLM: Stopped")
            self.llm_status_label.setStyleSheet("color: #f48771;")
            self.server_btn.setText("Start Server")
            self.server_btn.setStyleSheet("")
            self.stop_server_btn.setEnabled(False)
            self.stop_server_btn.setStyleSheet("")

    def populate_model_menu(self):
        """Populate the model selector submenu with discovered models."""
        if not self._model_menu:
            return
        self._model_menu.clear()

        server = get_llm_server()
        models = server.find_models()

        if not models:
            no_models = QAction("No models found", self)
            no_models.setEnabled(False)
            self._model_menu.addAction(no_models)

            hint = QAction("Place .gguf files in ~/models/", self)
            hint.setEnabled(False)
            self._model_menu.addAction(hint)

            self._model_menu.addSeparator()
            add_action = QAction("Add Model from File...", self)
            add_action.triggered.connect(self.add_model_from_file)
            self._model_menu.addAction(add_action)
            return

        config = get_config()
        current_model = config.llm.model_path

        for model in models:
            action = QAction(f"{model.name} ({model.size_gb:.1f} GB)", self)
            action.setCheckable(True)
            action.setChecked(str(model.path) == current_model)
            action.setData(str(model.path))
            action.triggered.connect(lambda checked, m=model: self.select_model(m))
            self._model_menu.addAction(action)

        self._model_menu.addSeparator()
        add_action = QAction("Add Model from File...", self)
        add_action.triggered.connect(self.add_model_from_file)
        self._model_menu.addAction(add_action)

    def select_model(self, model):
        """Select a model and update configuration."""
        from templatr.core.config import get_config_manager

        config_manager = get_config_manager()
        config_manager.config.llm.model_path = str(model.path)
        config_manager.save()

        self.status_message.emit(f"Selected model: {model.name}", 3000)

        server = get_llm_server()
        if server.is_running():
            QMessageBox.information(
                self.window(),
                "Model Changed",
                f"Model changed to {model.name}.\n\n"
                "Restart the server (LLM → Stop, then Start) "
                "to use the new model.",
            )

    def add_model_from_file(self):
        """Add a model from a local GGUF file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self.window(),
            "Select GGUF Model",
            str(Path.home()),
            "GGUF Models (*.gguf);;All Files (*)",
        )

        if not file_path:
            return

        source = Path(file_path)
        server = get_llm_server()
        dest_dir = server.get_models_dir()
        dest = dest_dir / source.name

        if dest.exists():
            QMessageBox.warning(
                self.window(),
                "Model Exists",
                f"A model with this name already exists:\n{dest}\n\n"
                "Please rename the file or remove the existing model.",
            )
            return

        file_size = source.stat().st_size
        size_gb = file_size / (1024**3)

        self._progress_dialog = QProgressDialog(
            f"Copying {source.name} ({size_gb:.1f} GB)...",
            "Cancel",
            0,
            100,
            self.window(),
        )
        self._progress_dialog.setWindowTitle("Adding Model")
        self._progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self._progress_dialog.setAutoClose(False)
        self._progress_dialog.setAutoReset(False)
        self._progress_dialog.setValue(0)

        self._copy_worker = ModelCopyWorker(source, dest)
        self._copy_worker.progress.connect(self._progress_dialog.setValue)
        self._copy_worker.finished.connect(self._on_model_copy_finished)
        self._progress_dialog.canceled.connect(self._on_model_copy_canceled)

        self._copy_worker.start()
        self._progress_dialog.show()

    def _on_model_copy_canceled(self):
        """Handle user canceling the copy operation."""
        if self._copy_worker and self._copy_worker.isRunning():
            self._copy_worker.cancel()
            self._copy_worker.wait(timeout=5000)

        self.status_message.emit("Model import canceled", 3000)

    def _on_model_copy_finished(self, success: bool, message: str):
        """Handle model copy completion."""
        if self._progress_dialog:
            self._progress_dialog.close()

        if success:
            from templatr.core.config import get_config_manager
            from templatr.integrations.llm import ModelInfo

            model_path = Path(message)
            model = ModelInfo.from_path(model_path)

            config_manager = get_config_manager()
            config_manager.config.llm.model_path = str(model_path)
            config_manager.save()

            QMessageBox.information(
                self.window(),
                "Model Added",
                f"Successfully added model:\n{model.name}\n\n"
                "The model is now selected and ready to use.",
            )
            self.status_message.emit(f"Added model: {model.name}", 3000)
        else:
            QMessageBox.critical(
                self.window(),
                "Import Failed",
                f"Failed to import model:\n\n{message}",
            )

    def open_hugging_face(self):
        """Open Hugging Face models page in browser."""
        QDesktopServices.openUrl(
            QUrl("https://huggingface.co/models?sort=trending&search=gguf")
        )
        self.status_message.emit("Opened Hugging Face in browser", 3000)
