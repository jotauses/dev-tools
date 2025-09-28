
#!/bin/bash
set -e

ICON="$HOME/.local/share/icons/dev-tools.png"
DESKTOP="$HOME/.local/share/applications/dev-tools.desktop"
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Removing desktop entry and icon..."
rm -f "$DESKTOP" "$ICON"
update-desktop-database "$HOME/.local/share/applications/"

rm -rf "$PROJECT_DIR/.venv"
echo "Virtual environment removed."

echo "Uninstallation completed."
