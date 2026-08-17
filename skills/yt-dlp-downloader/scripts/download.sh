#!/bin/bash
# yt-dlp download helper script
# Usage: ./download.sh [options] URL
#
# Options:
#   -p, --path PATH      Download path (default: $ROXY_WORKSPACE/downloads)
#   -a, --audio          Extract audio only (MP3)
#   -s, --subs           Download subtitles
#   -q, --quality NUM    Max video height (720, 1080, etc.)
#   -f, --format ID      Specific format ID
#   -l, --list           List available formats
#   -h, --help           Show this help

set -euo pipefail

# Default values
DOWNLOAD_PATH=""
AUDIO_ONLY=false
DOWNLOAD_SUBS=false
QUALITY=""
FORMAT_ID=""
LIST_FORMATS=false
EXTRA_ARGS=()
URL=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--path)
            DOWNLOAD_PATH="$2"
            shift 2
            ;;
        -a|--audio)
            AUDIO_ONLY=true
            shift
            ;;
        -s|--subs)
            DOWNLOAD_SUBS=true
            shift
            ;;
        -q|--quality)
            QUALITY="$2"
            shift 2
            ;;
        -f|--format)
            FORMAT_ID="$2"
            shift 2
            ;;
        -l|--list)
            LIST_FORMATS=true
            shift
            ;;
        -h|--help)
            head -15 "$0" | tail -13
            exit 0
            ;;
        *)
            URL="$1"
            shift
            ;;
    esac
done

# Check if URL is provided
if [[ -z "$URL" ]]; then
    echo "Error: No URL provided"
    echo "Usage: $0 [options] URL"
    exit 1
fi

# Check dependencies
if ! command -v yt-dlp &> /dev/null; then
    echo "Error: yt-dlp is not installed"
    echo "Install with: uv tool install yt-dlp"
    exit 1
fi

case "$URL" in
    *bilibili.com*|*b23.tv*|*bili2233.cn*)
        EXTRA_ARGS+=(--cookies-from-browser chromium+gnomekeyring --no-cache-dir)
        if [[ -z "$FORMAT_ID" && -z "$QUALITY" && "$AUDIO_ONLY" != true ]]; then
            FORMAT_ID="bv*+ba/b"
        fi
        ;;
    *youtube.com*|*youtu.be*|*music.youtube.com*)
        EXTRA_ARGS+=(--cookies-from-browser chromium+gnomekeyring)
        ;;
esac

# List formats only
if [[ "$LIST_FORMATS" == true ]]; then
    yt-dlp "${EXTRA_ARGS[@]}" -F "$URL"
    exit 0
fi

if [[ -z "$DOWNLOAD_PATH" ]]; then
    DOWNLOAD_PATH="${ROXY_WORKSPACE:?ROXY_WORKSPACE is required}/downloads"
fi

# Create download directory
mkdir -p "$DOWNLOAD_PATH"

CMD=(yt-dlp "${EXTRA_ARGS[@]}" -P "$DOWNLOAD_PATH" -o "%(title)s.%(ext)s")

# Add format selection
if [[ -n "$FORMAT_ID" ]]; then
    CMD+=(-f "$FORMAT_ID")
elif [[ -n "$QUALITY" ]]; then
    CMD+=(-f "bestvideo[height<=$QUALITY]+bestaudio/best[height<=$QUALITY]")
fi

# Audio extraction
if [[ "$AUDIO_ONLY" == true ]]; then
    if ! command -v ffmpeg &> /dev/null; then
        echo "Warning: ffmpeg not found. Audio extraction may fail."
        echo "Install with: sudo pacman -S ffmpeg  (or: sudo apt install ffmpeg)"
    fi
    CMD+=(-x --audio-format mp3)
fi

# Subtitles
if [[ "$DOWNLOAD_SUBS" == true ]]; then
    CMD+=(--write-subs --sub-langs all)
fi

# Add URL
CMD+=("$URL")

# Execute
printf 'Executing:'
printf ' %q' "${CMD[@]}"
echo
echo "Download path: $DOWNLOAD_PATH"
echo ""
"${CMD[@]}"

echo ""
echo "Download complete! Files saved to: $DOWNLOAD_PATH"
