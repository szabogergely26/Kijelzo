#!/bin/bash

set -e

PACKAGE_NAME="monitor-config-gui"
VERSION="0.1.0"
BUILD_DIR="build/${PACKAGE_NAME}_${VERSION}_all"
OUTPUT_DIR="dist"

rm -rf build
mkdir -p "$BUILD_DIR/DEBIAN"
mkdir -p "$OUTPUT_DIR"

cp packaging/deb/control "$BUILD_DIR/DEBIAN/control"
cp -a packaging/deb/root/. "$BUILD_DIR/"

find "$BUILD_DIR" -type d -exec chmod 755 {} \;

chmod 755 "$BUILD_DIR/usr/bin/monitor-config-gui"
chmod 755 "$BUILD_DIR/usr/share/monitor-config/kijelzo.sh"
chmod 644 "$BUILD_DIR/usr/share/monitor-config/monitor-config-gui.py"
chmod 644 "$BUILD_DIR/usr/share/applications/monitor-config-gui.desktop"

dpkg-deb --root-owner-group --build "$BUILD_DIR" "$OUTPUT_DIR/${PACKAGE_NAME}_${VERSION}_all.deb"

echo
echo "Elkészült:"
echo "$OUTPUT_DIR/${PACKAGE_NAME}_${VERSION}_all.deb"
