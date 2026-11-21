#!/bin/sh
set -eu
umask 022

root=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)
output=${1:-"$root/dist/release"}
mkdir -p -- "$output"
output=$(CDPATH='' cd -- "$output" && pwd)

version=$(cat "$root/VERSION")
if ! printf '%s\n' "$version" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+(rc[0-9]+)?$'; then
    printf '%s\n' 'VERSION must contain a Compass release version.' >&2
    exit 1
fi
debian_version=$(printf '%s' "$version" | sed 's/rc/~rc/')
stage=$(mktemp -d)
trap 'rm -r -- "$stage"' EXIT

package="$stage/package"
app="$package/usr/share/compass-desktop"
doc="$package/usr/share/doc/compass-desktop"
assets="$root/packaging/debian"
desktop=io.github.nuggar4_cmd.Compass

install -dm755 "$package/DEBIAN" "$app/compass" "$app/ui" "$doc"
install -m644 "$root/main.py" "$root/VERSION" "$app/"
install -m644 "$root"/compass/*.py "$app/compass/"
install -m644 "$root"/ui/*.html "$root"/ui/*.css "$root"/ui/*.js "$app/ui/"
install -m644 "$root/APPROVED_SITES.md" "$doc/"
install -m644 "$assets/copyright" "$doc/"
install -Dm755 "$assets/compass-desktop" "$package/usr/bin/compass-desktop"
install -Dm644 "$assets/$desktop.desktop" "$package/usr/share/applications/$desktop.desktop"
install -Dm644 "$assets/$desktop.svg" "$package/usr/share/icons/hicolor/scalable/apps/$desktop.svg"

size=$(du -sk -- "$package" | cut -f1)
cat > "$package/DEBIAN/control" <<EOF
Package: compass-desktop
Version: $debian_version
Section: utils
Priority: optional
Architecture: all
Maintainer: Compass contributors <noreply@github.com>
Installed-Size: $size
Depends: python3 (>= 3.11), python3-gi, gir1.2-gtk-3.0, gir1.2-webkit2-4.1 (>= 2.40)
Description: desktop catalog of software publisher websites
 Compass lets users find software by name or category and opens the approved
 publisher website in the default browser after a native confirmation.
Homepage: https://github.com/nuggar4-cmd/Compass-public
EOF

if [ -n "${SOURCE_DATE_EPOCH:-}" ]; then
    find "$package" -exec touch -h -d "@$SOURCE_DATE_EPOCH" {} +
fi

name="compass-desktop_${debian_version}_all.deb"
dpkg-deb --root-owner-group --build "$package" "$stage/$name"
install -m644 "$stage/$name" "$output/$name"
(cd "$output" && sha256sum "$name" > "$name.sha256")
