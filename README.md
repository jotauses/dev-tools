


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
   chmod +x install.sh uninstall.sh launcher.sh
   ./install.sh
   ```
   This will create the virtual environment, install dependencies, the icon and the application menu entry.

## Uninstallation

To remove menu entries, icon and the virtual environment:
```bash
./uninstall.sh
```

## Usage

- From terminal:
  ```bash
  ./launcher.sh
  ```
- From the application menu: search for "Dev Tools".

## Features
- Install/update VSCode (requires root only for that action)
- Install Python versions
- Create virtual environments
- System information

## Notes
- For privileged actions, `pkexec` is used (must be installed and configured on your system).
- Compatible with any user and Linux environment.
