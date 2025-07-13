#!/usr/bin/env sh
# Env Required:
# - SSHFS_URI: SSHFS uses this as the remote location to mount.
# - GOCRYPTFS_PASSWORD: The gocryptfs password
# - SSHFS_HOSTKEY: Use `ssh-keyscan -p 23 xxx.your-storagebox.de` to get this
# - SSHFS_KEY: The ssh private key file content
set -e

CRYPTFS_MOUNT="/mnt/gocryptfs"
SSHFS_MOUNT="/mnt/sshfs"
ENCRYPTED_DIR="$SSHFS_MOUNT/encrypted"

mkdir -p "$CRYPTFS_MOUNT" "$SSHFS_MOUNT"

SSH_KEY_FILE=$(mktemp)
chmod 600 "$SSH_KEY_FILE"
echo -e "$SSHFS_KEY" > "$SSH_KEY_FILE"
cat $SSH_KEY_FILE

KNOWN_HOSTS_FILE=$(mktemp)
echo -e "$SSHFS_HOSTKEY" > "$KNOWN_HOSTS_FILE"
cat $KNOWN_HOSTS_FILE

cleanup() {
    sync
    fusermount -u "$CRYPTFS_MOUNT" || true
    sync
    sleep 1
    fusermount -u "$SSHFS_MOUNT" || true
    rm -f "$SSH_KEY_FILE" "$KNOWN_HOSTS_FILE"
}
trap cleanup EXIT

sshfs \
    -o allow_other \
    -o IdentityFile="$SSH_KEY_FILE" \
    -o UserKnownHostsFile="$KNOWN_HOSTS_FILE" \
    -o StrictHostKeyChecking=yes \
    -p 23 \
      "${SSHFS_URI}" \
      "$SSHFS_MOUNT"

mkdir -p $ENCRYPTED_DIR

# Initialize gocryptfs if needed (only on first use)
if [ ! -f "$ENCRYPTED_DIR/gocryptfs.conf" ]; then
    echo "$GOCRYPTFS_PASSWORD" | gocryptfs -config $ENCRYPTED_DIR/gocryptfs.conf -init "$ENCRYPTED_DIR"
fi

echo "$GOCRYPTFS_PASSWORD" | gocryptfs "$ENCRYPTED_DIR" "$CRYPTFS_MOUNT"

python -u /app/main.py
