#!/usr/bin/env bash
# Update cockpit and cockpit-podman to a new version, rebuild RPMs,
# reinstall on host and push spec to GitHub fork.
set -euo pipefail

TOPDIR=/opt
REPO_DIR="$TOPDIR/SOURCES/cockpit"
INSTANCE="${INSTANCE:-fedora43-ai-f24}"
HOST_RPM_DIR="/opt/$INSTANCE/RPMS"

# ── Versions ─────────────────────────────────────────────────────────────────
COCKPIT_NEW="${1:-}"
PODMAN_NEW="${2:-}"

latest_github() {
    curl -s "https://api.github.com/repos/$1/releases/latest" | python3 -c "import sys,json; print(json.load(sys.stdin)['tag_name'])"
}

if [[ -z "$COCKPIT_NEW" ]]; then
    echo "→ Checking latest cockpit version..."
    COCKPIT_NEW=$(latest_github cockpit-project/cockpit)
fi
if [[ -z "$PODMAN_NEW" ]]; then
    echo "→ Checking latest cockpit-podman version..."
    PODMAN_NEW=$(latest_github cockpit-project/cockpit-podman)
fi

COCKPIT_OLD=$(rpmspec -q --qf '%{version}\n' "$TOPDIR/SPECS/cockpit.spec" 2>/dev/null | head -1)
PODMAN_OLD=$(rpmspec -q --qf '%{version}\n' "$TOPDIR/SPECS/cockpit-podman.spec" 2>/dev/null | head -1)

echo "cockpit:       $COCKPIT_OLD → $COCKPIT_NEW"
echo "cockpit-podman: $PODMAN_OLD → $PODMAN_NEW"

if [[ "$COCKPIT_NEW" == "$COCKPIT_OLD" && "$PODMAN_NEW" == "$PODMAN_OLD" ]]; then
    echo "✓ Already up to date. Nothing to do."
    exit 0
fi

# ── Download sources ──────────────────────────────────────────────────────────
download() {
    local url="$1" dest="$2"
    if [[ ! -f "$dest" ]]; then
        echo "→ Downloading $(basename "$dest")..."
        curl -L -o "$dest" "$url"
    else
        echo "✓ $(basename "$dest") already present."
    fi
}

if [[ "$COCKPIT_NEW" != "$COCKPIT_OLD" ]]; then
    BASE="https://github.com/cockpit-project/cockpit/releases/download/$COCKPIT_NEW"
    download "$BASE/cockpit-$COCKPIT_NEW.tar.xz"      "$TOPDIR/SOURCES/cockpit-$COCKPIT_NEW.tar.xz"
    download "$BASE/cockpit-node-$COCKPIT_NEW.tar.xz" "$TOPDIR/SOURCES/cockpit-node-$COCKPIT_NEW.tar.xz"
    sed -i "s/^Version:.*/Version:        $COCKPIT_NEW/" "$TOPDIR/SPECS/cockpit.spec"
fi

if [[ "$PODMAN_NEW" != "$PODMAN_OLD" ]]; then
    BASE="https://github.com/cockpit-project/cockpit-podman/releases/download/$PODMAN_NEW"
    download "$BASE/cockpit-podman-$PODMAN_NEW.tar.xz"      "$TOPDIR/SOURCES/cockpit-podman-$PODMAN_NEW.tar.xz"
    download "$BASE/cockpit-podman-node-$PODMAN_NEW.tar.xz" "$TOPDIR/SOURCES/cockpit-podman-node-$PODMAN_NEW.tar.xz"
    sed -i "s/^Version:.*/Version:        $PODMAN_NEW/" "$TOPDIR/SPECS/cockpit-podman.spec"
fi

# ── Build ─────────────────────────────────────────────────────────────────────
echo "→ Building cockpit RPMs..."
rpmbuild --define "_topdir $TOPDIR" -bb "$TOPDIR/SPECS/cockpit.spec"

echo "→ Building cockpit-podman RPM..."
rpmbuild --define "_topdir $TOPDIR" -bb "$TOPDIR/SPECS/cockpit-podman.spec"

# ── Install on host ───────────────────────────────────────────────────────────
echo "→ Installing on host (via bind-mounted $HOST_RPM_DIR)..."

# noarch packages via dnf upgrade
dnf upgrade -y \
    "$HOST_RPM_DIR/noarch/cockpit-bridge-$COCKPIT_NEW"*.rpm \
    "$HOST_RPM_DIR/noarch/cockpit-system-$COCKPIT_NEW"*.rpm \
    "$HOST_RPM_DIR/noarch/cockpit-networkmanager-$COCKPIT_NEW"*.rpm \
    "$HOST_RPM_DIR/noarch/cockpit-storaged-$COCKPIT_NEW"*.rpm \
    "$HOST_RPM_DIR/noarch/cockpit-podman-$PODMAN_NEW"*.rpm \
    "$HOST_RPM_DIR/x86_64/cockpit-$COCKPIT_NEW"*.rpm 2>/dev/null || true

# cockpit-ws needs --nodeps (versioned ELF symbol provides issue on OpenMandriva)
rpm -Uvh --nodeps "$HOST_RPM_DIR/x86_64/cockpit-ws-$COCKPIT_NEW"*.rpm

echo "→ Restarting cockpit..."
# runs on host via systemd
systemctl try-restart cockpit.socket 2>/dev/null || true

# ── Push to GitHub ────────────────────────────────────────────────────────────
echo "→ Pushing updated specs to GitHub fork..."

\cp "$TOPDIR/SPECS/cockpit.spec"        "$REPO_DIR/cockpit.spec"
\cp "$TOPDIR/SPECS/cockpit-podman.spec" "$REPO_DIR/cockpit-podman.spec"

git -C "$REPO_DIR" add cockpit.spec cockpit-podman.spec
git -C "$REPO_DIR" commit -m "Update cockpit to $COCKPIT_NEW, cockpit-podman to $PODMAN_NEW" \
    --author="safrano9999 <fortschritt24.kontakt@gmail.com>"
# Push via gh token if available, otherwise remind user
if command -v gh &>/dev/null && gh auth status &>/dev/null 2>&1; then
    git -C "$REPO_DIR" push origin update-to-360.1
else
    echo ""
    echo "⚠ GitHub nicht eingeloggt — push manuell im Fedora-Container:"
    echo "  git -C $REPO_DIR push origin update-to-360.1"
fi

echo ""
echo "✓ Done!"
echo "  cockpit        $COCKPIT_NEW"
echo "  cockpit-podman $PODMAN_NEW"
echo "  Fork: https://github.com/safrano9999/cockpit"
