#!/usr/bin/env python3

from __future__ import annotations
import sys
import os
import re
import shutil
import signal
import subprocess
import platform
import mimetypes
import tempfile
import textwrap
from pathlib import Path

__version__ = "1.0.1"

# yes this is hardcoded its a free api :3

GROQ_API_KEY = "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"
GROQ_URL     = "https://api.groq.com/openai/v1/audio/transcriptions"
GROQ_MODEL   = "whisper-large-v3"

SUPPORTS_COLOR = (
    hasattr(sys.stdout, "isatty")
    and sys.stdout.isatty()
    and os.environ.get("NO_COLOR") is None\
)
def _c(code, t): return f"\033[{code}m{t}\033[0m" if SUPPORTS_COLOR else t
def bold(t): return _c("1", t)
def dim(t): return _c("2", t)
def green(t): return _c("32", t)
def cyan(t): return _c("36", t)
def yellow(t): return _c("33", t)
def red(t): return _c("31", t)
def magenta(t): return _c("35", t)
def out(*a, **k): print(*a, **k, flush=True)

LOGO = r"""
  ███████╗███████╗███╗   ███╗
  ██╔════╝██╔════╝████╗ ████║
  ███████╗█████╗  ██╔████╔██║
  ╚════██║██╔══╝  ██║╚██╔╝██║
  ███████║██║     ██║ ╚═╝ ██║
  ╚══════╝╚═╝     ╚═╝     ╚═╝
     simple file manipulator!
"""

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff",
              ".tif", ".ico", ".avif", ".heic", ".heif"}
AUDIO_EXTS = {".mp3", ".wav", ".flac", ".aac", ".ogg", ".opus", ".m4a",
              ".wma", ".aiff", ".aif"}
VIDEO_EXTS = {".mp4", ".mkv", ".webm", ".avi", ".mov", ".flv", ".wmv",
              ".ts", ".m2ts", ".3gp", ".m4v"}
DOC_EXTS   = {".pdf", ".docx", ".doc", ".txt", ".md", ".html", ".htm",
              ".odt", ".rtf", ".epub"}

# most-used formats listed first per type
CONVERT_TARGETS = {
    "image": ["webp", "jpg", "png", "gif", "bmp", "tiff", "ico", "avif"],
    "audio": ["mp3",  "aac", "flac", "wav", "opus", "ogg",  "m4a"],
    "video": ["mp4",  "mkv", "webm", "avi", "mov",  "gif"],
    "doc":   ["txt",  "pdf", "html", "md",  "docx"],
}

COMPRESS_PRESETS = {
    "image": [
        ("Web        < 100 KB",  {"quality": 72, "max_w": 1920}),
        ("Balanced   < 500 KB",  {"quality": 85, "max_w": 3840}),
        ("High       < 1.5 MB",  {"quality": 92, "max_w": None}),
        ("Lossless PNG",         {"lossless": True}),
    ],
    "video": [
        ("Tiny   – 360p  (CRF 35)", {"height": 360,  "crf": 35}),
        ("Small  – 480p  (CRF 28)", {"height": 480,  "crf": 28}),
        ("Medium – 720p  (CRF 23)", {"height": 720,  "crf": 23}),
        ("Large  – 1080p (CRF 18)", {"height": 1080, "crf": 18}),
        ("Minimal loss   (CRF 15)", {"height": None, "crf": 15}),
    ],
    "audio": [
        ("Voice / Podcast   64k",  {"bitrate": "64k"}),
        ("Standard         128k",  {"bitrate": "128k"}),
        ("High Quality     192k",  {"bitrate": "192k"}),
        ("Studio           320k",  {"bitrate": "320k"}),
    ],
}

def detect_type(path):
    ext = path.suffix.lower()
    if ext in IMAGE_EXTS: return "image"
    if ext in AUDIO_EXTS: return "audio"
    if ext in VIDEO_EXTS: return "video"
    if ext in DOC_EXTS:   return "doc"
    mime, _ = mimetypes.guess_type(str(path))
    if mime:
        if mime.startswith("image/"): return "image"
        if mime.startswith("audio/"): return "audio"
        if mime.startswith("video/"): return "video"
        if mime.startswith("application/"): return "doc"
    return "unknown"
def require_dep(name, hint):
    if shutil.which(name):
        return True
    out(red(f"\n  x {name} not found."))
    out(dim(f"    install: {hint}"))
    return False
def clear_screen():
    os.system("cls" if platform.system() == "Windows" else "clear")
def _pause():
    try:
        input(dim("\n. press enter to continue..."))
    except (EOFError, KeyboardInterrupt):
        pass
def unique_path(p):
    if not p.exists():
        return p
    stem, suffix, i = p.stem, p.suffix, 1
    while True:
        c = p.with_name(f"{stem}_({i}){suffix}")
        if not c.exists():
            return c
        i += 1
def ask_file(prompt="  paste file path :3 --> ", given=None):
    if given is not None:
        return given
    while True:
        try:
            raw = input(magenta(prompt)).strip()
        except (EOFError, KeyboardInterrupt):
            out()
            return None
        if not raw:
            continue
        raw = raw.strip("'\"")   # handle drag-and-drop quoting
        p = Path(raw).expanduser().resolve()
        if p.exists() and p.is_file():
            return p
        out(red(f"  ✗ file not found: {raw}"))

def _copy_to_clipboard(text):
    sys_name = platform.system()
    try:
        if sys_name == "Darwin": # why is macos named darwin anyways
            subprocess.run(["pbcopy"], input=text.encode(), check=True)
            out(green("  ✓ copied to clipboard!"))
        elif sys_name == "Linux":
            if shutil.which("xclip"):
                subprocess.run(["xclip", "-selection", "clipboard"], input=text.encode(), check=True)
                out(green("  ✓ copied to clipboard!"))
            elif shutil.which("xsel"):
                subprocess.run(["xsel", "--clipboard", "--input"], input=text.encode(), check=True)
                out(green("  ✓ copied to clipboard!"))
            else:
                out(yellow("  ! install xclip or xsel for clipboard support!"))
        elif sys_name == "Windows":
            subprocess.run(["clip"], input=text.encode("utf-16"), check=True)
            out(green("  ✓ copied to clipboard!"))
    except Exception as e:
        out(yellow(f"  ! failed to copy to clipboard: {e}"))

# remove bg

def do_remove_bg(given=None):
    out()
    out(bold("  -- Remove Background --"))
    out(dim("  uses local ML tool, meaning your pics stay on your machine! :D"))
    out()

    try:
        from rembg import remove as rembg_remove
        from PIL import Image  # noqa: F401
    except ImportError:
        out(red("  x missing dependencies!!"))
        out(dim("    pip install rembg Pillow"))
        _pause()
        return

    path = ask_file(given=given)
    if not path:
        return
    
    if detect_type(path) != "image":
        out(red("  x not an image file!"))
        _pause()
        return
    
    out(cyan(f"\n  --> gooning and removing background from {path.name}..."))

    try:
        result = rembg_remove(path.read_bytes())
        out_path = unique_path(path.with_name(f"{path.stem}_nobg.png"))
        out_path.write_bytes(result)
        out(green(f"  ✓ saved to {out_path.name}!"))
    except Exception as e:
        out(red(f"  x failed: {e}"))

    _pause()


# convert format --> format

def do_convert(given=None):
    out()
    out(bold("  -- Convert --"))
    out()

    path = ask_file(given=given)
    if not path:
        return
    
    ftype = detect_type(path)
    if ftype == "unknown":
        out(red("  x could not detect file type: {path.suffix}!"))
        _pause()
        return
    
    current = path.suffix.lower().lstrip(".")
    targets = [t for t in CONVERT_TARGETS.get(ftype, []) if t != current]

    out()
    out(cyan(f"  {path.name}  ({ftype})"))
    out(bold("  convert to:"))
    out()
    for i, fmt in enumerate(targets, 1):
        out(f"    {dim(str(i)+'.')} {fmt}")
    out()

    try:
        idx = int(choice) - 1
    except ValueError:
        out(red("  x invalid choice!"))
        _pause()
        return

    if not (0 <= idx < len(targets)):
        out(red("  x choice out of range!"))
        _pause()
        return
    
    target_fmt = targets[idx]
    out_path = unique_path(path.with_suffix(f".{target_fmt}"))
    out(cyan(f"\n  --> converting to {target_fmt}..."))

    try:
        if ftype == "image":
            _convert_image(path, out_path, target_fmt)
        elif ftype in ("audio", "video"):
            _convert_media(path, out_path, target_fmt, ftype)
        elif ftype == "doc":
            _convert_doc(path, out_path)
        out(green(f"  ✓ saved to {out_path.name}!"))
    except Exception as e:
        out(red(f"  x failed: {e}"))

    _pause()

if __name__ == "__main__":
    main()