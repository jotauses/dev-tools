import os
import subprocess
from typing import List, Optional

VENV_NAME = ".venv"
TEMP_DIR = "/tmp/dev-tools"
BACKUP_DIR = "/opt/vscode-backup"
VSCODE_PATH = "/opt/vscode"


class DevToolsService:
    @staticmethod
    def detect_python_versions() -> List[str]:
        """Detect installed Python versions (robust, cross-environment)."""
        import glob
        import re

        versions = set()
        # ...existing code...

    @staticmethod
    def get_python_command(version: str) -> Optional[str]:
        if subprocess.call(["which", f"python{version}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
            return f"python{version}"
        try:
            result = subprocess.run(
                ["compgen", "-c", "python"], capture_output=True, text=True, shell=True, executable="/bin/bash"
            )
            for cmd in set(result.stdout.split()):
                try:
                    version_out = subprocess.run([cmd, "--version"], capture_output=True, text=True)
                    if version_out.returncode == 0:
                        v = version_out.stdout.strip().split()[-1]
                        v = ".".join(v.split(".")[:2])
                        if v == version:
                            return cmd
                except Exception:
                    continue
        except Exception:
            pass
        if subprocess.call(["which", "python3"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
            return "python3"
        if subprocess.call(["which", "python"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
            return "python"
        return None

    @staticmethod
    def update_vscode(progress_callback=None) -> str:
        import shutil
        import time

        if not os.path.isdir(VSCODE_PATH):
            return "VSCode not found in /opt/vscode"
        backup_timestamp = time.strftime("%Y%m%d_%H%M%S")
        temp_dir = TEMP_DIR
        try:
            if progress_callback:
                progress_callback(10, "Downloading...")
            os.makedirs(temp_dir, exist_ok=True)
            subprocess.run(
                [
                    "wget",
                    "-q",
                    "--show-progress",
                    "-O",
                    "vscode.tar.gz",
                    "https://code.visualstudio.com/sha/download?build=stable&os=linux-x64",
                ],
                cwd=temp_dir,
                check=True,
            )
            if progress_callback:
                progress_callback(70, "Updating as root...")
            script_path = os.path.join(os.path.dirname(__file__), "update_vscode_root.sh")
            # Ensure script is executable
            os.chmod(script_path, 0o755)
            result = subprocess.run(
                ["pkexec", script_path, backup_timestamp], cwd=temp_dir, capture_output=True, text=True
            )
            if result.returncode == 0 and result.stdout.startswith("OK:"):
                if progress_callback:
                    progress_callback(100, "Completed")
                return "VSCode updated successfully."
            else:
                msg = result.stdout.strip() or result.stderr.strip()
                return f"Error updating VSCode: {msg}"
        except Exception as e:
            return f"Error: {e}"

    @staticmethod
    def install_python(version: str, progress_callback=None) -> str:
        if not version.startswith("3."):
            return "Invalid version. Examples: 3.11, 3.12, 3.13"
        # ...existing code...

    @staticmethod
    def system_info() -> str:
        sys_info = []
        sys_info.append(f"System: {subprocess.getoutput('uname -srm')}")
        sys_info.append(f"Kernel: {subprocess.getoutput('uname -v').split()[0:3]}")
        # Python
        python_versions = DevToolsService.detect_python_versions()
        if python_versions:
            sys_info.append("Python installed:")
            for version in python_versions:
                py_cmd = DevToolsService.get_python_command(version)
                if py_cmd:
                    ver = subprocess.getoutput(f"{py_cmd} --version")
                    sys_info.append(f"• {py_cmd}: {ver}")
        else:
            sys_info.append("Python: Not installed")
        # VSCode
        if os.path.isfile(f"{VSCODE_PATH}/bin/code"):
            vscode_version = subprocess.getoutput(f"{VSCODE_PATH}/bin/code --version").splitlines()[0]
            sys_info.append(f"VSCode: {vscode_version}")
        else:
            sys_info.append("VSCode: Not installed")
        # Disk
        disk_info = subprocess.getoutput("df -h / | awk 'NR==2 {print $4 \" free of \" $2}'")
        sys_info.append(f"Disk: {disk_info}")
        # Memory
        mem_info = subprocess.getoutput("free -h | awk 'NR==2 {print $7 \" free of \" $2}'")
        sys_info.append(f"Memory: {mem_info}")
        # Backups
        if os.path.isdir(BACKUP_DIR) and os.listdir(BACKUP_DIR):
            backup_count = len(os.listdir(BACKUP_DIR))
            sys_info.append(f"VSCode Backups: {backup_count}")
        return "\n".join(sys_info)
