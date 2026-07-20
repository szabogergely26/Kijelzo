#!/bin/bash

set -e
# Mindig a projekt gyökeréből dolgozunk, akkor is,
# ha a scriptet a packaging/deb mappából indítjuk.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"

# Név, verzió:
PACKAGE_NAME="monitor-config"
VERSION="0.1.2"
BUILD_DIR="build/${PACKAGE_NAME}_${VERSION}_all"
OUTPUT_DIR="dist"

rm -rf build
mkdir -p "$BUILD_DIR/DEBIAN"
mkdir -p "$OUTPUT_DIR"

cp packaging/deb/control "$BUILD_DIR/DEBIAN/control"
cp -a packaging/deb/root/. "$BUILD_DIR/"

# Programfájlok csomagolása
mkdir -p "$BUILD_DIR/usr/share/monitor-config"

cp main.py "$BUILD_DIR/usr/share/monitor-config/main.py"
cp -a monitor_config "$BUILD_DIR/usr/share/monitor-config/"

find "$BUILD_DIR" -type d -exec chmod 755 {} \;

# jogosultság beállítása
chmod 755 "$BUILD_DIR/usr/bin/monitor-config"
chmod 644 "$BUILD_DIR/usr/share/monitor-config/main.py"
find "$BUILD_DIR/usr/share/monitor-config/monitor_config" -type f -exec chmod 644 {} \;
find "$BUILD_DIR/usr/share/monitor-config/monitor_config" -type d -exec chmod 755 {} \;
chmod 644 "$BUILD_DIR/usr/share/applications/monitor-config.desktop"

dpkg-deb --root-owner-group --build "$BUILD_DIR" "$OUTPUT_DIR/${PACKAGE_NAME}_${VERSION}_all.deb"

echo
echo "Elkészült:"
echo "$OUTPUT_DIR/${PACKAGE_NAME}_${VERSION}_all.deb"
