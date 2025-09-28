import subprocess
from pathlib import Path

from PyQt6.QtCore import QObject, Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QPixmap
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from services.dev_tools_service import DevToolsService


class Worker(QObject):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:

            def progress_cb(val, msg):
                self.progress.emit(val, msg)

            self.kwargs["progress_callback"] = progress_cb
            result = self.func(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dev Tools")
        self.setMinimumSize(540, 400)
        self.setStyleSheet(self._get_styles())
        self._init_ui()
        self._active_threads = []

    def _init_ui(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout()

        header = QHBoxLayout()
        logo = QLabel()
        logo_path = Path(__file__).parent.parent / "icon.png"

        if logo_path.exists() and not QPixmap(str(logo_path)).isNull():
            logo.setPixmap(
                QPixmap(str(logo_path)).scaled(
                    48, 48, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
                )
            )
        else:
            logo.setText("")

        title = QLabel("<b>Dev Tools</b>")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        header.addWidget(logo)
        header.addWidget(title)
        header.addItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        main_layout.addLayout(header)

        tabs = QTabWidget()
        tabs.addTab(self._vscode_tab(), QIcon(), "VSCode")
        tabs.addTab(self._python_tab(), QIcon(), "Python")
        tabs.addTab(self._venv_tab(), QIcon(), "Virtualenvs")
        tabs.addTab(self._system_tab(), QIcon(), "System")
        main_layout.addWidget(tabs)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    def _vscode_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        desc = QLabel("Install or update Visual Studio Code on your system.")
        desc.setWordWrap(True)
        btn_update = QPushButton(QIcon.fromTheme("system-software-update"), "Install/Update VSCode")
        btn_update.setToolTip("Download, install or update VSCode in /opt/vscode")
        btn_update.clicked.connect(self._update_vscode)
        layout.addWidget(desc)
        layout.addWidget(btn_update)
        layout.addStretch()
        tab.setLayout(layout)
        return tab

    def _python_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        desc = QLabel("Install a specific version of Python on your system.")
        desc.setWordWrap(True)
        btn_install = QPushButton(QIcon.fromTheme("applications-python"), "Install Python")
        btn_install.setToolTip("Install a Python version using pacman or by compiling from source")
        btn_install.clicked.connect(self._install_python)
        layout.addWidget(desc)
        layout.addWidget(btn_install)
        layout.addStretch()
        tab.setLayout(layout)
        return tab

    def _venv_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        desc = QLabel("Create a Python virtual environment in the directory you choose.")
        desc.setWordWrap(True)
        btn_create = QPushButton(QIcon.fromTheme("folder-new"), "Create virtual environment")
        btn_create.setToolTip("Create a Python virtual environment in the selected directory")
        btn_create.clicked.connect(self._create_venv)
        layout.addWidget(desc)
        layout.addWidget(btn_create)
        layout.addStretch()
        tab.setLayout(layout)
        return tab

    def _system_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        desc = QLabel("System information and installed tools.")
        desc.setWordWrap(True)
        btn_info = QPushButton(QIcon.fromTheme("dialog-information"), "Show system information")
        btn_info.setToolTip("Show relevant system and tools information")
        btn_info.clicked.connect(self._show_system_info)
        layout.addWidget(desc)
        layout.addWidget(btn_info)
        layout.addStretch()
        tab.setLayout(layout)
        return tab

    def _execute_task(self, task_func, *args, title="Task", label="Processing..."):
        dlg = QProgressDialog(label, None, 0, 100, self)
        dlg.setWindowTitle(title)
        dlg.setValue(0)
        dlg.setMinimumDuration(0)
        dlg.setCancelButton(None)

        worker = Worker(task_func, *args)
        thread = QThread()

        self._active_threads.append((worker, thread))
        worker.moveToThread(thread)

        def handle_finished(result):
            dlg.setValue(100)
            QMessageBox.information(self, title, result)
            dlg.close()
            thread.quit()
            thread.wait(1000)
            if (worker, thread) in self._active_threads:
                self._active_threads.remove((worker, thread))
            worker.deleteLater()
            thread.deleteLater()

        def handle_error(error_msg):
            dlg.close()
            QMessageBox.critical(self, f"{title} Error", f"An error occurred:\n{error_msg}")
            thread.quit()
            if (worker, thread) in self._active_threads:
                self._active_threads.remove((worker, thread))
            worker.deleteLater()
            thread.deleteLater()

        def handle_progress(val, msg):
            dlg.setValue(val)
            dlg.setLabelText(msg)

        worker.progress.connect(handle_progress)
        worker.finished.connect(handle_finished)
        worker.error.connect(handle_error)

        thread.started.connect(worker.run)
        thread.start()

    def _update_vscode(self):
        self._execute_task(DevToolsService.update_vscode, title="VSCode", label="Updating VSCode...")

    def _create_venv(self):
        path = QFileDialog.getExistingDirectory(self, "Select the directory for the virtual environment")
        if not path:
            return

        available_versions = DevToolsService.detect_python_versions()
        if not available_versions:
            QMessageBox.warning(self, "No Python Versions", "No Python versions found on your system.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Select Python Version")
        dialog.setMinimumWidth(400)

        layout = QVBoxLayout()

        info_label = QLabel("Choose Python version for virtual environment:")
        layout.addWidget(info_label)

        version_combo = QComboBox()

        version_details = []
        for version in available_versions:
            python_cmd = DevToolsService.get_python_command(version)
            if python_cmd:
                try:
                    result = subprocess.run([python_cmd, "--version"], capture_output=True, text=True, check=False)
                    exact_version = result.stdout.strip() if result.returncode == 0 else f"Python {version}"
                    display_text = f"{exact_version} ({python_cmd})"
                    version_details.append((display_text, version))
                except Exception:
                    display_text = f"Python {version} ({python_cmd})"
                    version_details.append((display_text, version))

        version_details.sort(key=lambda x: tuple(map(int, x[1].split("."))), reverse=True)

        for display_text, version in version_details:
            version_combo.addItem(display_text, version)

        layout.addWidget(version_combo)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        dialog.setLayout(layout)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        selected_version = version_combo.currentData()

        self._execute_task(
            DevToolsService.create_venv,
            path,
            selected_version,
            title="Virtual Environment",
            label=f"Creating virtual environment with Python {selected_version}...",
        )

    def _install_python(self):
        version, ok = QInputDialog.getText(self, "Install Python", "Python version (e.g.: 3.11):", text="3.11")
        if not ok or not version:
            return
        self._execute_task(
            DevToolsService.install_python, version, title="Python", label=f"Installing Python {version}..."
        )

    def _show_system_info(self):
        info = DevToolsService.system_info()
        QMessageBox.information(self, "System Information", info)

    def _get_styles(self):
        return """
        QMainWindow {
            background: #23272e;
        }
        QLabel, QTabWidget::tab {
            color: #e0e0e0;
        }
        QPushButton {
            background: #3b4252;
            color: #e0e0e0;
            border-radius: 6px;
            padding: 8px 16px;
            font-size: 15px;
        }
        QPushButton:hover {
            background: #5e81ac;
        }
        QTabWidget::pane {
            border: 1px solid #444;
            border-radius: 8px;
        }
        QTabBar::tab {
            background: #2e3440;
            color: #e0e0e0;
            padding: 8px 20px;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
            margin-right: 2px;
        }
        QTabBar::tab:selected {
            background: #5e81ac;
            color: #fff;
        }
        QProgressDialog {
            background: #23272e;
            color: #e0e0e0;
        }
        """
