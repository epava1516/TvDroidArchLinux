#!/usr/bin/env bash
# shellcheck disable=SC2034
iso_name="archtv-lab"
iso_label="ARCHTV_LAB"
iso_publisher="Arch TV project"
iso_application="Arch TV development and installation laboratory"
iso_version="0.1.0"
install_dir="arch"
bootmodes=('uefi.systemd-boot')
pacman_conf="pacman.conf"
airootfs_image_type="squashfs"
airootfs_image_tool_options=('-comp' 'zstd' '-Xcompression-level' '6')
file_permissions=(["/etc/shadow"]="0:0:400")
