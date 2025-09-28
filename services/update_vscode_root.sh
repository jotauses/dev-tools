#!/bin/bash
set -e

VSCODE_PATH="/opt/vscode"
BACKUP_DIR="/opt/vscode-backup"
TEMP_DIR="/tmp/dev-tools"
BACKUP_TIMESTAMP="$1"
CURRENT_BACKUP="$BACKUP_DIR/$BACKUP_TIMESTAMP"

# 1. Backup
mkdir -p "$BACKUP_DIR"
cp -r "$VSCODE_PATH" "$CURRENT_BACKUP"


# 2. Remove old VSCode
rm -rf "$VSCODE_PATH"

# 3. Extract and move new VSCode
cd "$TEMP_DIR"
tar -xzf vscode.tar.gz
mv VSCode-linux-x64 "$VSCODE_PATH"

# 4. Verify
if [ ! -f "$VSCODE_PATH/bin/code" ]; then
    rm -rf "$VSCODE_PATH"
    mv "$CURRENT_BACKUP" "$VSCODE_PATH"
    echo "ERROR: Update failed, backup restored: $CURRENT_BACKUP"
    exit 1
fi

# 5. Cleanup: keep only the 3 most recent backups (excluding the current one)
cd "$BACKUP_DIR"
backups=( $(ls -dt */ 2>/dev/null | grep -v "/$BACKUP_TIMESTAMP/" | head -n 3) )
for b in $(ls -d */ 2>/dev/null | grep -v "/$BACKUP_TIMESTAMP/"); do
    skip=0
    for keep in "${backups[@]}"; do
        [[ "$b" == "$keep" ]] && skip=1 && break
    done
    [[ $skip -eq 0 ]] && rm -rf "$b"
done

# 6. Remove the backup just created (only if update succeeded)
rm -rf "$CURRENT_BACKUP"

echo "OK: VSCode updated successfully"