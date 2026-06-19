#!/bin/bash

set -e

# Név, verzió:
PACKAGE_NAME="monitor-config"
VERSION="0.1.0"
BUILD_DIR="build/${PACKAGE_NAME}_${VERSION}_all"
OUTPUT_DIR="dist"

rm -rf build
mkdir -p "$BUILD_DIR/DEBIAN"
mkdir -p "$OUTPUT_DIR"

cp packaging/deb/control "$BUILD_DIR/DEBIAN/control"
cp -a packaging/deb/root/. "$BUILD_DIR/"

find "$BUILD_DIR" -type d -exec chmod 755 {} \;

# jogosultság beállítása
chmod 755 "$BUILD_DIR/usr/bin/monitor-config"
chmod 644 "$BUILD_DIR/usr/share/monitor-config/monitor_config.py"
chmod 644 "$BUILD_DIR/usr/share/applications/monitor-config.desktop"

dpkg-deb --root-owner-group --build "$BUILD_DIR" "$OUTPUT_DIR/${PACKAGE_NAME}_${VERSION}_all.deb"

echo
echo "Elkészült:"
echo "$OUTPUT_DIR/${PACKAGE_NAME}_${VERSION}_all.deb"
