#!/bin/sh

if ! which jar >/dev/null; then
    echo "$0: jar not found" >&2
    echo "apt-get install --no-install-recommends openjdk-7-jdk" >&2
    exit 1
fi

tika_server_jar=$(readlink -f "$1")
timeout=$2

ocr_properties=org/apache/tika/parser/ocr/TesseractOCRConfig.properties

test -e "$tika_server_jar" || exit 1
test -n "$timeout" || exit 1

tmp_dir=$(mktemp -d)
cd "$tmp_dir"

jar xf "$tika_server_jar" "$ocr_properties"
sed -i "s/^timeout=.*$/timeout=${timeout}/" "$ocr_properties"
jar uf "$tika_server_jar" "$ocr_properties"

rm -rf "$tmp_dir"
