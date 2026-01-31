#!/bin/bash
# Creates a minimal valid MP4 for integration tests (1s black video)
set -e
OUT_DIR="${1:-./integration-test-videos}"
mkdir -p "$OUT_DIR"
ffmpeg -f lavfi -i "color=c=black:s=320x240:d=1" -pix_fmt yuv420p -y "$OUT_DIR/sample.mp4" 2>/dev/null
echo "Created $OUT_DIR/sample.mp4"
