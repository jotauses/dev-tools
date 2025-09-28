import logging
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Callable, List, Optional

VENV_NAME = ".venv"
TEMP_DIR = Path("/tmp/dev-tools")
BACKUP_DIR = Path("/opt/vscode-backup")
VSCODE_PATH = Path("/opt/vscode")
VSCODE_DOWNLOAD_URL = "https://code.visualstudio.com/sha/download?build=stable&os=linux-x64"

logger = logging.getLogger(__name__)


class SystemCommandError(Exception):
    pass


class DevToolsService:
    PYTHON_PATHS = ["/usr/bin", "/usr/local/bin", "/opt/homebrew/bin", os.path.expanduser("~/.local/bin")]

    @staticmethod
    def _run_command(cmd: List[str], check: bool = True, **kwargs) -> subprocess.CompletedProcess:
        try:
            result = subprocess.run(cmd, check=check, capture_output=True, text=True, **kwargs)
            return result
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {e.cmd}, error: {e.stderr}")
            raise SystemCommandError(f"Command '{e.cmd}' failed: {e.stderr}") from e
        except FileNotFoundError as e:
            logger.error(f"Command not found: {cmd[0]}")
            raise SystemCommandError(f"Command '{cmd[0]}' not found") from e

    @staticmethod
    def _find_python_executables() -> List[Path]:
        python_patterns = ["python*", "python3*"]
        executables = []

        for path in DevToolsService.PYTHON_PATHS:
            if not os.path.isdir(path):
                continue
            try:
                for pattern in python_patterns:
                    for file_path in Path(path).glob(pattern):
                        if file_path.is_file() and os.access(file_path, os.X_OK):
                            real_path = file_path.resolve()
                            if real_path not in executables:
                                executables.append(real_path)
            except OSError:
                continue

        return executables

    @staticmethod
    def detect_python_versions() -> List[str]:
        version_pattern = re.compile(r"python(\d+\.\d+(?:\.\d+)?)")
        found_versions = set()

        for executable in DevToolsService._find_python_executables():
            match = version_pattern.match(executable.name)
            if match:
                found_versions.add(match.group(1))
                continue

            try:
                result = DevToolsService._run_command([str(executable), "--version"], check=False)
                if result.returncode == 0:
                    version_output = result.stdout.strip()
                    version_match = re.search(r"(\d+\.\d+\.\d+)", version_output)
                    if version_match:
                        found_versions.add(version_match.group(1))
                    else:
                        version_match = re.search(r"(\d+\.\d+)", version_output)
                        if version_match:
                            found_versions.add(version_match.group(1))
            except (SystemCommandError, Exception):
                continue

        return sorted(found_versions, key=lambda v: tuple(map(int, v.split("."))))

    @staticmethod
    def get_python_command(version: str) -> Optional[str]:
        python_cmd = f"python{version}"
        try:
            result = DevToolsService._run_command(["which", python_cmd], check=False)
            if result.returncode == 0:
                return python_cmd
        except SystemCommandError:
            pass

        for executable in DevToolsService._find_python_executables():
            try:
                result = DevToolsService._run_command([str(executable), "--version"], check=False)
                if result.returncode == 0:
                    output_version = result.stdout.strip().split()[-1]
                    if output_version.startswith(version):
                        return executable.name
            except (SystemCommandError, Exception):
                continue

        return None

    @staticmethod
    def update_vscode(progress_callback: Optional[Callable[[int, str], None]] = None) -> str:
        import time

        if not VSCODE_PATH.exists():
            return "VSCode not found in /opt/vscode"

        backup_timestamp = time.strftime("%Y%m%d_%H%M%S")
        temp_dir = TEMP_DIR / f"vscode_update_{backup_timestamp}"

        try:
            temp_dir.mkdir(parents=True, exist_ok=True)

            if progress_callback:
                progress_callback(10, "Downloading VSCode...")

            download_path = temp_dir / "vscode.tar.gz"
            try:
                DevToolsService._run_command(
                    ["wget", "-q", "--show-progress", "-O", str(download_path), VSCODE_DOWNLOAD_URL]
                )
            except SystemCommandError as e:
                return f"Download failed: {e}"

            if progress_callback:
                progress_callback(70, "Updating VSCode...")

            script_path = Path(__file__).parent / "update_vscode_root.sh"
            if not script_path.exists():
                return f"Update script not found: {script_path}"

            script_path.chmod(0o755)

            result = DevToolsService._run_command(
                ["pkexec", str(script_path), backup_timestamp], check=False, cwd=temp_dir
            )

            if result.returncode == 0 and result.stdout.strip().startswith("OK:"):
                if progress_callback:
                    progress_callback(100, "Update completed")
                return "VSCode updated successfully."
            else:
                error_msg = result.stderr.strip() or result.stdout.strip()
                return f"Update failed: {error_msg}"

        except Exception as e:
            logger.error(f"VSCode update error: {e}")
            return f"Error updating VSCode: {e}"
        finally:
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)

    @staticmethod
    def _install_from_package_manager(version: str) -> bool:
        try:
            result = DevToolsService._run_command(["pacman", "-Ss", f"python{version}"], check=False)
            if result.returncode == 0 and f"python{version}" in result.stdout:
                DevToolsService._run_command(["sudo", "pacman", "-S", "--noconfirm", f"python{version}"])
                return True

            result = DevToolsService._run_command(["apt-cache", "search", f"python{version}"], check=False)
            if result.returncode == 0 and f"python{version}" in result.stdout:
                DevToolsService._run_command(["sudo", "apt", "update"])
                DevToolsService._run_command(["sudo", "apt", "install", "-y", f"python{version}"])
                return True

        except SystemCommandError:
            pass

        return False

    @staticmethod
    def _install_from_source(version: str, progress_callback: Optional[Callable[[int, str], None]] = None) -> bool:
        source_dir = TEMP_DIR / f"python_source_{version}"

        try:
            source_dir.mkdir(parents=True, exist_ok=True)

            if progress_callback:
                progress_callback(40, "Installing build dependencies...")

            try:
                DevToolsService._run_command(
                    ["sudo", "pacman", "-S", "--noconfirm", "--needed", "base-devel", "wget", "tk"]
                )
            except SystemCommandError:
                DevToolsService._run_command(["sudo", "apt", "update"])
                DevToolsService._run_command(
                    ["sudo", "apt", "install", "-y", "build-essential", "wget", "tk-dev", "libssl-dev"]
                )

            if progress_callback:
                progress_callback(60, "Downloading Python source...")

            python_url = f"https://www.python.org/ftp/python/{version}/Python-{version}.tar.xz"
            archive_path = source_dir / f"Python-{version}.tar.xz"

            DevToolsService._run_command(["wget", "-q", "--show-progress", "-O", str(archive_path), python_url])

            if progress_callback:
                progress_callback(75, "Extracting source...")

            DevToolsService._run_command(["tar", "-xf", str(archive_path)], cwd=source_dir)

            build_dir = source_dir / f"Python-{version}"

            if progress_callback:
                progress_callback(80, "Configuring build...")

            DevToolsService._run_command(
                ["./configure", "--enable-optimizations", "--with-ensurepip=install"], cwd=build_dir
            )

            if progress_callback:
                progress_callback(85, "Compiling Python...")

            cpu_count = os.cpu_count() or 1
            DevToolsService._run_command(["make", f"-j{cpu_count}"], cwd=build_dir)

            if progress_callback:
                progress_callback(95, "Installing...")

            DevToolsService._run_command(["sudo", "make", "altinstall"], cwd=build_dir)
            return True

        except SystemCommandError as e:
            logger.error(f"Source installation failed: {e}")
            return False
        finally:
            if source_dir.exists():
                shutil.rmtree(source_dir, ignore_errors=True)

    @staticmethod
    def install_python(version: str, progress_callback: Optional[Callable[[int, str], None]] = None) -> str:
        try:
            if not re.match(r"^\d+\.\d+$", version):
                return f"Invalid Python version format: {version}"

            if progress_callback:
                progress_callback(20, "Checking package manager...")

            if DevToolsService._install_from_package_manager(version):
                if progress_callback:
                    progress_callback(100, "Installation completed")
                return f"Python {version} installed via package manager."

            if progress_callback:
                progress_callback(30, "Package not found, building from source...")

            if DevToolsService._install_from_source(version, progress_callback):
                if progress_callback:
                    progress_callback(100, "Installation completed")
                return f"Python {version} installed from source."

            return "Failed to install Python from both package manager and source."

        except Exception as e:
            logger.error(f"Python installation error: {e}")
            return f"Error installing Python: {e}"

    @staticmethod
    def create_venv(
        target_dir: str, python_version: str, progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> str:
        python_cmd = DevToolsService.get_python_command(python_version)
        if not python_cmd:
            return f"Python {python_version} not found."

        venv_path = Path(target_dir) / VENV_NAME
        try:
            if progress_callback:
                progress_callback(10, f"Creating virtual environment with {python_cmd}...")
            result = DevToolsService._run_command([python_cmd, "-m", "venv", str(venv_path)])
            if result.returncode == 0:
                if progress_callback:
                    progress_callback(100, "Virtual environment created successfully.")
                return f"Virtual environment created at {venv_path} using {python_cmd}."
            return f"Failed to create virtual environment: {result.stderr.strip()}"
        except Exception as e:
            logger.error(f"Error creating virtual environment: {e}")
            return f"Error creating virtual environment: {e}"

    @staticmethod
    def system_info() -> str:
        info_lines = []

        try:
            info_lines.append(f"System: {subprocess.getoutput('uname -srm')}")

            python_versions = DevToolsService.detect_python_versions()
            if python_versions:
                info_lines.append("Python versions installed:")
                for version in python_versions:
                    py_cmd = DevToolsService.get_python_command(version)
                    if py_cmd:
                        try:
                            ver_output = DevToolsService._run_command([py_cmd, "--version"], check=False)
                            info_lines.append(f"• {py_cmd}: {ver_output.stdout.strip()}")
                        except SystemCommandError:
                            info_lines.append(f"• {py_cmd}: version check failed")
            else:
                info_lines.append("Python: Not installed")

            vscode_binary = VSCODE_PATH / "bin" / "code"
            if vscode_binary.exists():
                try:
                    vscode_version = DevToolsService._run_command([str(vscode_binary), "--version"], check=False)
                    info_lines.append(f"VSCode: {vscode_version.stdout.splitlines()[0]}")
                except SystemCommandError:
                    info_lines.append("VSCode: Installed (version check failed)")
            else:
                info_lines.append("VSCode: Not installed")

            disk_info = subprocess.getoutput("df -h / | awk 'NR==2 {print $4 \" free of \" $2}'")
            info_lines.append(f"Disk: {disk_info}")

            mem_info = subprocess.getoutput("free -h | awk 'NR==2 {print $7 \" free of \" $2}'")
            info_lines.append(f"Memory: {mem_info}")

            if BACKUP_DIR.exists():
                backup_count = len(list(BACKUP_DIR.iterdir()))
                info_lines.append(f"VSCode Backups: {backup_count}")

        except Exception as e:
            logger.error(f"Error gathering system info: {e}")
            info_lines.append(f"Error gathering system information: {e}")

        return "\n".join(info_lines)
