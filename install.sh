# this is basically copied from syt lmaooo

#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SFM_PY="$SCRIPT_DIR/sfm.py"

if [ ! -f "$SFM_PY" ]; then
    echo "error: sfm.py not found in $SCRIPT_DIR!"
    exit 1
fi

echo ""
echo "  installing sfm... hold tight! :3"
echo ""

# loca
if [ -d "$HOME/.local/bin" ] || mkdir -p "$HOME/.local/bin" 2>/dev/null; then
    INSTALL_DIR="$HOME/.local/bin"
elif [ -w "/usr/local/bin" ]; then
    INSTALL_DIR="/usr/local/bin"
else
    INSTALL_DIR="$HOME/.local/bin"
    mkdir -p "$INSTALL_DIR"
fi

WRAPPER="$INSTALL_DIR/sfm"
cat > "$WRAPPER" <<WRAPPER_EOF
#!/bin/sh
exec python3 "$SFM_PY" "\$@"
WRAPPER_EOF

chmod +x "$WRAPPER"
chmod +x "$SFM_PY"

SHELL_NAME="$(basename "$SHELL")"
case "$SHELL_NAME" in
    zsh)  RC="$HOME/.zshrc" ;;
    bash) RC="$HOME/.bashrc" ;;
    fish) RC="$HOME/.config/fish/config.fish" ;;
    *)    RC="$HOME/.profile" ;;
esac

if ! echo "$PATH" | tr ':' '\n' | grep -qx "$INSTALL_DIR"; then
    echo "  adding $INSTALL_DIR to PATH in $RC..."
    echo "" >> "$RC"
    if [ "$SHELL_NAME" = "fish" ]; then
        echo "set -gx PATH $INSTALL_DIR \$PATH" >> "$RC"
    else
        echo "export PATH=\"$INSTALL_DIR:\$PATH\"" >> "$RC"
    fi
fi

# dependencies
echo "  installing python dependencies..."
echo ""

DEPS="rembg Pillow requests trafilatura"

python3 -m pip install --quiet --break-system-packages $DEPS 2>/dev/null \
    || python3 -m pip install --quiet $DEPS 2>/dev/null \
    || {
        echo ""
        echo "  ⚠  pip install failed — try manually:"
        echo "     pip install $DEPS"
    }

# triple check ffMPREG
if ! command -v ffmpeg &>/dev/null; then
    echo ""
    echo "  ⚠  ffmpeg not found (needed for convert, compress, transcribe)"
    if [ "$(uname)" = "Darwin" ]; then
        echo "     brew install ffmpeg"
    else
        echo "     sudo apt install ffmpeg"
    fi
fi

echo ""
echo "  ✓ sfm installed to $WRAPPER"
echo ""
echo "  restart your terminal (or: source $RC)"
echo "  then run:  sfm  :3"
echo ""
