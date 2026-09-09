#!/bin/sh
# Preview only: no reboot, boot environment changes, or block-device writes.
set -eu
menu=${1:?Usage: preview.sh /absolute/path/to/km6-menu}
case "$menu" in /*) ;; *) echo 'Use an absolute executable path' >&2; exit 2 ;; esac
test -x "$menu"
test "$(id -u)" = 0
oldvt=$(fgconsole)
trap 'chvt "$oldvt"' EXIT
trap 'exit 2' INT TERM HUP
openvt -c 8 -s -w -- env TERM=linux sh -c '
    stty sane -ixon -ixoff
    setfont /usr/share/consolefonts/Lat15-TerminusBold32x16.psf.gz
    setterm --blank 0
    # Without --foreground, timeout creates a background process group;
    # tcsetattr then stops the menu with SIGTTOU before it draws anything.
    timeout --foreground 180 "$1" --timeout 150
    result=$?
    echo "Menu preview result: $result" > /run/km6-menu-result
' sh "$menu"
