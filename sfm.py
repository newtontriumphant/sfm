#!/usr/bin/env python3

from __future__ import annotations
from py_compile import main
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

def _convert_image(src, dst, fmt):
    from PIL import Image
    img = Image.open(src)

    if fmt in ("jpg", "jpeg"):
        if img.mode in ("RGBA", "P", "LA"):
            bg = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            mask = img.split()[-1] if img.mode in ("RGBA", "LA") else None
            bg.paste(img, mask=mask)
            img = bg
        else:
            img = img.convert("RGB")
    elif fmt not in ("png", "gif", "ico", "tiff", "tif", "bmp", "webp", "avif"):
        img = img.convert("RGB")

    kw = {}
    if fmt == "webp":
        kw = {"quality": 90, "method": 6}
    elif fmt in ("jpg", "jpeg"):
        kw = {"quality": 95, "optimize": True}
    elif fmt == "png":
        kw = {"optimize": True}
    img.save(dst, **kw)

def _convert_media(src, dst, fmt, src_type):
    if not require_dep("ffmpeg", "brew install ffmpeg  /  sudo apt install ffmpeg"):
        raise RuntimeError("ffmpeg not found")
    
    # video --> gif special exc.
    if fmt == "gif":
        palette = dst.with_suffix(".palette.png")
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(src), "-i", str(palette), "-lavfi",
             "fps=15,scale=480:-1:flags=lanczos[x];[x][1:v]paletteuse", str(dst)],
             capture_output=True, check=True)
        palette.unlink(missing_ok=True)
        return
    
    # these args are AI-gen :3
    audio_args = {
        "mp3":  ["-c:a", "libmp3lame", "-q:a", "0"],
        "aac":  ["-c:a", "aac",        "-b:a", "192k"],
        "flac": ["-c:a", "flac"],
        "wav":  ["-c:a", "pcm_s16le"],
        "opus": ["-c:a", "libopus",    "-b:a", "128k"],
        "ogg":  ["-c:a", "libvorbis",  "-q:a", "6"],
        "m4a":  ["-c:a", "aac",        "-b:a", "192k",
                 "-movflags", "+faststart"],
    }
    video_args = {
        "mp4":  ["-c:v", "libx264", "-crf", "18", "-preset", "slow",
                 "-c:a", "aac",     "-b:a", "192k", "-movflags", "+faststart"],
        "mkv":  ["-c:v", "libx264", "-crf", "18", "-preset", "slow",
                 "-c:a", "aac"],
        "webm": ["-c:v", "libvpx-vp9", "-crf", "30", "-b:v", "0",
                 "-c:a", "libopus"],
        "avi":  ["-c:v", "libx264", "-crf", "18", "-c:a", "mp3"],
        "mov":  ["-c:v", "libx264", "-crf", "18", "-preset", "slow",
                 "-c:a", "aac"],
    }

    cmd = ["ffmpeg", "-y", "-i", str(src)]
    if fmt in audio_args:
        if src_type == "video":
            cmd.append("-vn")
        cmd += audio_args[fmt]
    elif fmt in video_args:
        cmd += video_args[fmt]
    cmd.append(str(dst))

    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.decode()[-500:])

def _convert_doc(src, dst):
    if not require_dep("pandoc", "brew install pandoc  /  sudo apt install pandoc"):
        raise RuntimeError("pandoc not found")
    
    r = subprocess.run(["pandoc", str(src), "-o", str(dst)], capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.decode()[-500:])
    
# transcribe a/v to text!

def do_transcribe(given=None):
    out()
    out(bold("  -- Transcribe --"))
    out()

    path = ask_file(given=given)
    if not path:
        return
    
    ftype = detect_type(path)
    if ftype not in ("audio", "video"):
        out(red("  x not an audio/video file!"))
        _pause()
        return

    try:
        import requests
    except ImportError:
        out(red("  x missing dependency!!"))
        out(dim("    pip install requests"))
        _pause()
        return
    
    temp_audio = None
    upload_path = path

    if ftype == "video":
        if not require_dep("ffmpeg", "brew install ffmpeg  /  sudo apt install ffmpeg"):
            _pause()
            return
        out(cyan("  --> gooning and extracting audio..."))
        tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        tmp.close()
        temp_audio = Path(tmp.name)
        r = subprocess.run(
            ["ffmpeg", "-y", "-i", str(path), "-vn",
             "-c:a", "libmp3lame", "-q:a", "4", str(temp_audio)],
             capture_output=True)
        if r.returncode != 0:
            out(red("  x failed to extract audio!"))
            temp_audio.unlink(missing_ok=True)
            _pause()
            return
        upload_path = temp_audio

    try:
        size_kb = upload_path.stat().st_size // 1024
        out(cyan(f"  --> uploading to groq! file size: ({size_kb:,} KB)..."))

        with open(upload_path, "rb") as f:
            resp = requests.post(
                GROQ_URL,
                headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                files={"file": (upload_path.name, f, "audio/mpeg")},
                data={"model": GROQ_MODEL, "response_format": "text"},
                timeout=180,
            )
        resp.raise_for_status()
        transcript = resp.text.strip()

        words = len(transcript.split())
        out(green(f"  ✓ transcription complete! word count: {words}"))
        out()
        out(dim("  -" * 30))
        out()
        for line in transcript.split("\n"):
            if line.strip():
                out(textwrap.fill(line.strip(), width=70,
                                    initial_indent="  ",
                                    subsequent_indent="  "))
            else:
                out()
        out()
        out(dim("  -" * 30))
        out()

        out(f"  {bold('s.')} Save to .txt  "
            f"  {bold('c.')} Copy to clipboard  "
            f"  {bold('enter.')} Back")
        out()
        try:
            act = input(cyan("  --> ")).strip().lower()
        except (EOFError, KeyboardInterrupt):
            return
            
        if act == "s":
            op = unique_path(path.with_suffix(".txt"))
            op.write_text(transcript, encoding="utf-8")
            out(green(f"  ✓ saved to {op.name}!"))
        elif act == "c":
            _copy_to_clipboard(transcript)

    except Exception as e:
        out(red(f"  x transcription failed: {e}"))
    finally:
        if temp_audio:
            temp_audio.unlink(missing_ok=True)
        
    _pause()

# compression!

def do_compress(given=None):
    out()
    out(bold("  -- Compress --"))
    out()

    path = ask_file(given=given)
    if not path:
        return
    
    ftype = detect_type(path)
    if ftype not in COMPRESS_PRESETS:
        out(red("  x compression not supported for {ftype} files, sorry!"))
        _pause()
        return
    
    size_kb = path.stat().st_size // 1024
    out()
    out(cyan(f"  {path.name}  ({size_kb:,} KB)"))
    out(bold("  pick a preset:"))
    out()

    presets = COMPRESS_PRESETS[ftype]
    for i, (label, _) in enumerate(presets, 1):
        out(f"    {dim(str(i) + '.')} {label}")
    out()

    try:
        choice = input(cyan("  --> ")).strip()
    except (EOFError, KeyboardInterrupt):
        return

    try:
        idx = int(choice) - 1
    except ValueError:
        out(red("  x invalid choice!"))
        _pause()
        return

    if not (0 <= idx < len(presets)):
        out(red("  x invalid choice!"))
        _pause()
        return
    
    label, params = presets[idx]
    out(cyan(f"\n  --> compressing with preset: '{label}'..."))

    try:
        if ftype == "image":
            op = unique_path(path.with_name(f"{path.stem}_compressed{path.suffix}"))
            _compress_image(path, op, params)
        elif ftype == "video":
            op = unique_path(path.with_name(f"{path.stem}_compressed.mp4"))
            _compress_video(path, op, params)
        elif ftype == "audio":
            op = unique_path(path.with_name(f"{path.stem}_compressed.mp3"))
            _compress_audio(path, op, params)

        new_kb = op.stat().st_size // 1024
        saved_pct = int((size_kb - new_kb) / max(size_kb, 1) * 100)
        out(green(f"  ✓ saved → {op.name}"))
        out(dim(f"     {size_kb:,} KB → {new_kb:,} KB  (−{saved_pct}%)"))
    except Exception as e:
        out(red(f"  x compression failed: {e}"))

    _pause()

# helpers

def _compress_image(src, dst, params):
    from PIL import Image
    img = Image.open(src)

    if params.get("lossless"):
        img.save(dst, format="PNG", optimize=True)
        return
    
    if params.get("max_w") and img.width > params["max_w"]:
        ratio = params["max_w"] / img.width
        img = img.resize(
            (params["max_w"], int(img.height * ratio)), Image.LANCZOS)

    q = params.get("quality", 85)
    fmt = dst.suffix.lower().lstrip(".")
    if fmt in ("jpg", "jpeg"):
        img = img.convert("RGB")
        img.save(dst, quality=q, optimize=True)
    elif fmt == "webp":
        img.save(dst, quality=q, method=6)
    else:
        img.save(dst, quality=q)

def _compress_video(src, dst, params):
    if not require_dep("ffmpeg", "brew install ffmpeg  /  sudo apt install ffmpeg"):
        raise RuntimeError("ffmpeg not found")

    cmd = ["ffmpeg", "-y", "-i", str(src)]
    if params.get("height"):
        cmd += ["-vf", f"scale=-2:{params['height']}"]
    cmd += [
        "-c:v", "libx264",
        "-crf", str(params.get("crf", 23)),
        "-preset", "slow",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        str(dst),
    ]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.decode()[-500:])

def _compress_audio(src, dst, params):
    if not require_dep("ffmpeg", "brew install ffmpeg  /  sudo apt install ffmpeg"):
        raise RuntimeError("ffmpeg not found")
    
    r = subprocess.run(
        ["ffmpeg", "-y", "-i", str(src),
         "-c:a", "libmp3lame", "-b:a", params["bitrate"], str(dst)], capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.decode()[-500:])
    
# ah yes! paywall bypasser & readability!

def do_readable(url=None):
    out()
    out(bold("  -- Readable --"))
    out(dim("  strips ads, paywalls, and noise from any link!"))
    out()

    if not url:
        try:
            url = input(magenta("  paste url! --> ")).strip()
        except (EOFError, KeyboardInterrupt):
            return
    if not urn:
        return
    
    try:
        import trafilatura
    except ImportError:
        out(red("  x missing dependency!!"))
        out(dim("    pip install trafilatura"))
        _pause()
        return
    
    try:
        import requests
    except ImportError:
        out(red("  x missing dependency!!"))
        out(dim("    pip install requests"))
        _pause()
        return
    
    out(cyan("  --> fetching..."))
    text = title = None

    # first try
    try:
        dl = trafilatura.fetch_url(url)
        if dl:
            text = trafilatura.extract(
                dl, include_comments=False, include_tables=True,
                no_fallback=False, favor_precision=True)
            meta = trafilatura.extract_metadata(dl)
            if meta:
                title = meta.title
            if text and len(text.strip()) < 200:
                text = None
    except Exception:
        pass
    
    # pass 2 googlebot

    if not text:
        out(dim("  --> trying googlebot!"))
        try:
            r = requests.get(url, headers={
                "User-Agent": (
                    "Mozilla/5.0 (compatible; Googlebot/2.1; "
                    " +http://www.google.com/bot.html)"
                ),
                "Accept": "text/html,application/xhtml+xml",
            }, timeout=15)

            if r.ok:
                text = trafilatura.extract(r.text, favor_precision=True)
                if text and len(text.strip()) < 200:
                    text = None
                if not title:
                    meta = trafilatura.extract_metadata(r.text)
                    if meta:
                        title = meta.title
        except Exception:
            pass
    
    # pass 3 12ft

    if not text:
        out(dim("  --> trying 12ft proxy!"))
        try:
            r = requests.get(f"https://12ft.io/proxy?q={url}",
                             headers={"User-Agent": "Mozilla/5.0"},
                             timeout=15)
            if r.ok:
                text = trafilatura.extract(r.text, favor_precision=True)
                if text and len(text.strip()) < 200:
                    text = None
        except Exception:
            pass

    # final pass, archive.ph

    if not text:
        out(dim("  --> trying archive.ph!"))
        try:
            r = requests.get(
                f"https://archive.ph/newest/{url}",
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=20, allow_redirects=True)
            if r.ok:
                text = trafilatura.extract(r.text, favor_precision=True)
                if text and len(text.strip()) < 200:
                    text = None
        except Exception:
            pass

    if not text:
        out(red("  x could not extract readable content."))
        out(dim("    heavy JS rendering or aggressive DRM may be blocking this."))
        _pause()
        return

    words = len(text.split())
    mins  = max(1, words // 200)

    out(green(f"  ✓ extracted  ({words:,} words · ~{mins} min read)!"))
    if title:
        out(dim(f"  title: {title}"))
    out()
    out(dim("  -" * 30))
    out()

    for para in text.split("\n"):
        if para.strip():
            out(textwrap.fill(
                para.strip(), width=72,
                initial_indent="  ", subsequent_indent="  "))
        else:
            out()
    out()
    out(dim("  -" * 30))
    out()
    out(f"  {bold('s.')} Save to .txt    {bold('enter.')} Back")
    out()

    try:
        act = input(cyan("  --> ")).strip().lower()
    except (EOFError, KeyboardInterrupt):
        return
    
    if act == "s":
        safe = re.sub(r"[^\w\s-]", "", title or url)[:60].strip().replace(" ", "_")
        op = unique_path(Path.cwd() / f"{safe or 'article'}.txt")
        header = f"{title}\n{'=' * len(title)}\n\n" if title else ""
        op.write_text(header + text, encoding="utf-8")
        out(green(f"  ✓ saved → {op.name}"))

    _pause()

# finally done. ANYWAYS, MAIN MENU NEXT!

def main_menu():
    while True:
        clear_screen()

def main():
    main_menu()

if __name__ == "__main__":
    main()