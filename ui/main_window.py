import os

from PyQt6.QtCore import QObject, Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QPixmap
from PyQt6.QtWidgets import (
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

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        def progress_cb(val, msg):
            self.progress.emit(val, msg)

        self.kwargs["progress_callback"] = progress_cb
        result = self.func(*self.args, **self.kwargs)
        self.finished.emit(result)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dev Tools")
        self.setMinimumSize(540, 400)
        self.setStyleSheet(self._qss())
        self._init_ui()

    def _init_ui(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout()

        # Header with logo and title
        header = QHBoxLayout()
        logo = QLabel()
        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "icon.png")
        logo_path = os.path.normpath(logo_path)
        if QPixmap(logo_path).isNull():
            logo.setText("")
        else:
            logo.setPixmap(
                QPixmap(logo_path).scaled(
                    48, 48, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
                )
            )
        title = QLabel("<b>Dev Tools</b>")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        header.addWidget(logo)
        header.addWidget(title)
        header.addItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        main_layout.addLayout(header)

        # Tabs
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
        btn_update.clicked.connect(self.update_vscode)
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
        btn_install.clicked.connect(self.install_python)
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
        btn_create.clicked.connect(self.create_venv)
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
        btn_info.clicked.connect(self.system_info)
        layout.addWidget(desc)
        layout.addWidget(btn_info)
        layout.addStretch()
        tab.setLayout(layout)
        return tab

    def update_vscode(self):
        dlg = QProgressDialog("Actualizando VSCode...", None, 0, 100, self)
        dlg.setWindowTitle("VSCode")
        dlg.setValue(0)
        dlg.setMinimumDuration(0)
        dlg.setCancelButton(None)
        worker = Worker(DevToolsService.update_vscode)
        thread = QThread()
        worker.moveToThread(thread)
        worker.progress.connect(lambda val, msg: (dlg.setValue(val), dlg.setLabelText(msg)))
        worker.finished.connect(
            lambda result: (
                dlg.setValue(100),
                QMessageBox.information(self, "VSCode", result),
                thread.quit(),
                worker.deleteLater(),
                thread.deleteLater(),
            )
        )
        thread.started.connect(worker.run)
        thread.start()

    def create_venv(self):
        path = QFileDialog.getExistingDirectory(self, "Select the directory for the virtual environment")
        if not path:
            return
        dlg = QProgressDialog("Creating virtual environment...", None, 0, 100, self)
        dlg.setWindowTitle("Virtual Environment")
        dlg.setValue(0)
        dlg.setMinimumDuration(0)
        dlg.setCancelButton(None)
        worker = Worker(DevToolsService.create_venv, path)
        thread = QThread()
        worker.moveToThread(thread)
        worker.progress.connect(lambda val, msg: (dlg.setValue(val), dlg.setLabelText(msg)))
        worker.finished.connect(
            lambda result: (
                dlg.setValue(100),
                QMessageBox.information(self, "Virtual Environment", result),
                thread.quit(),
                worker.deleteLater(),
                thread.deleteLater(),
            )
        )
        thread.started.connect(worker.run)
        thread.start()

    def install_python(self):
        version, ok = QInputDialog.getText(self, "Install Python", "Python version (e.g.: 3.11):", text="3.11")
        if not ok or not version:
            return
        dlg = QProgressDialog(f"Installing Python {version}...", None, 0, 100, self)
        dlg.setWindowTitle("Python")
        dlg.setValue(0)
        dlg.setMinimumDuration(0)
        dlg.setCancelButton(None)
        worker = Worker(DevToolsService.install_python, version)
        thread = QThread()
        worker.moveToThread(thread)
        worker.progress.connect(lambda val, msg: (dlg.setValue(val), dlg.setLabelText(msg)))
        worker.finished.connect(
            lambda result: (
                dlg.setValue(100),
                QMessageBox.information(self, "Python", result),
                thread.quit(),
                worker.deleteLater(),
                thread.deleteLater(),
            )
        )
        thread.started.connect(worker.run)
        thread.start()

    def system_info(self):
        info = DevToolsService.system_info()
        QMessageBox.information(self, "System information", info)

    def _qss(self):
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

    def system_info(self):
        info = DevToolsService.system_info()
        QMessageBox.information(self, "System Info", info)

    def _init_ui(self):
        layout = QVBoxLayout()
        btn_update_vscode = QPushButton("Update VSCode")
        btn_create_venv = QPushButton("Create Virtual Environment")
        btn_install_python = QPushButton("Install Python")
        btn_system_info = QPushButton("System Info")
        btn_exit = QPushButton("Exit")

        btn_update_vscode.clicked.connect(self.update_vscode)
        btn_create_venv.clicked.connect(self.create_venv)
        btn_install_python.clicked.connect(self.install_python)
        btn_system_info.clicked.connect(self.system_info)
        btn_exit.clicked.connect(self.close)

        layout.addWidget(btn_update_vscode)
        layout.addWidget(btn_create_venv)
        layout.addWidget(btn_install_python)
        layout.addWidget(btn_system_info)
        layout.addWidget(btn_exit)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)


class Worker(QObject):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(str)

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        def progress_cb(val, msg):
            self.progress.emit(val, msg)

        self.kwargs["progress_callback"] = progress_cb
        result = self.func(*self.args, **self.kwargs)
        self.finished.emit(result)

    def update_vscode(self):
        dlg = QProgressDialog("Updating VSCode...", None, 0, 100, self)
        dlg.setWindowTitle("Update VSCode")
        dlg.setValue(0)
        dlg.setMinimumDuration(0)
        dlg.setCancelButton(None)

        worker = Worker(DevToolsService.update_vscode)
        thread = QThread()
        worker.moveToThread(thread)
        worker.progress.connect(lambda val, msg: (dlg.setValue(val), dlg.setLabelText(msg)))
        worker.finished.connect(
            lambda result: (
                dlg.setValue(100),
                QMessageBox.information(self, "Update VSCode", result),
                thread.quit(),
                worker.deleteLater(),
                thread.deleteLater(),
            )
        )
        thread.started.connect(worker.run)
        thread.start()

    def create_venv(self):
        path = QFileDialog.getExistingDirectory(self, "Select directory for virtual environment")
        if not path:
            return
        dlg = QProgressDialog("Creating virtual environment...", None, 0, 100, self)
        dlg.setWindowTitle("Create Virtual Environment")
        dlg.setValue(0)
        dlg.setMinimumDuration(0)
        dlg.setCancelButton(None)

        worker = Worker(DevToolsService.create_venv, path)
        thread = QThread()
        worker.moveToThread(thread)
        worker.progress.connect(lambda val, msg: (dlg.setValue(val), dlg.setLabelText(msg)))
        worker.finished.connect(
            lambda result: (
                dlg.setValue(100),
                QMessageBox.information(self, "Create Virtual Environment", result),
                thread.quit(),
                worker.deleteLater(),
                thread.deleteLater(),
            )
        )
        thread.started.connect(worker.run)
        thread.start()

    def install_python(self):
        version, ok = QInputDialog.getText(self, "Install Python", "Python version (e.g. 3.11):", text="3.11")
        if not ok or not version:
            return
        dlg = QProgressDialog(f"Installing Python {version}...", None, 0, 100, self)
        dlg.setWindowTitle("Install Python")
        dlg.setValue(0)
        dlg.setMinimumDuration(0)
        dlg.setCancelButton(None)

        worker = Worker(DevToolsService.install_python, version)
        thread = QThread()
        worker.moveToThread(thread)
        worker.progress.connect(lambda val, msg: (dlg.setValue(val), dlg.setLabelText(msg)))
