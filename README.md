


# Dev Tools

Cross-platform development tools for Python and VSCode, with a modern graphical interface (PyQt6).

## Quick Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/jotauses/dev-tools
   cd dev-tools
   ```
2. Run the installer:
   ```bash
   chmod +x install.sh uninstall.sh dev-tools-launcher.sh
   ./install.sh
   ```
   This will create the virtual environment, install dependencies, the icon and the application menu entry.

## Uninstallation

To remove menu entries, icon and (optionally) the virtual environment:
```bash
./uninstall.sh
```

## Usage

- From terminal:
  ```bash
  ./dev-tools-launcher.sh
  ```
- From the application menu: search for "Dev Tools".

## Portability
- No absolute paths or user references.
- The launcher and .desktop work in any folder.
- The icon is searched relative to the project or by name in the system.

## Features
- Install/update VSCode (requires root only for that action)
- Install Python versions
- Create virtual environments
- System information

## Notes
- For privileged actions, `pkexec` is used (must be installed and configured on your system).
- Compatible with any user and Linux environment.

---

Contributions and improvements are welcome.
