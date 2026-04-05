# sfm

## What is SFM?!

If you've ever heard of [SYT (Simple YouTube Downloader)](https://github.com/newtontriumphant/syt), this is basically that but for files!

SFM (Simple File Manipulator) is a simple program that runs natively in your terminal and lets you convert, compress, transcribe, and clean up files — without the pain of memorizing ffmpeg flags!

But why should I need to explain it to you when you could just watch a [**DEMO**](https://youtu.be/ZyHNC5oL1pg)?!

Have you ever needed to quickly convert a video, strip a background, or transcribe an audio file? If so, you've probably Googled "free online converter" and got jumpscared by 20 separate malware advertisement tabs opening, OR you tried to use `ffmpeg` directly and gave up after seeing how many arguments you needed to convert ONE file.

SFM fixes all your troubles. SFM is fully open-source, 100% free, and so simple that even your grandmother could probably figure out how to use it.

In addition to format conversion, SFM can remove backgrounds from images, transcribe audio and video to text, compress files across all types, and even strip ads and paywalls from any URL to give you a clean readable version!

## Requirements

- **Git**
- **Python 3.10+**
- **ffmpeg** —
Windows: [ffmpeg.org](https://ffmpeg.org/download.html) Mac: `brew install ffmpeg`
Linux: `sudo apt install ffmpeg`
- **pandoc** *(doc conversion only)* —
Windows: [pandoc.org](https://pandoc.org/installing.html) Mac: `brew install pandoc`
Linux: `sudo apt install pandoc`

Python dependencies are installed automatically by the install script, but if needed:

`pip install rembg Pillow requests trafilatura`

## Installation

**macOS / Linux:**

Step 1: Open your terminal and clone this repository locally:

```bash
git clone https://github.com/newtontriumphant/sfm
```

Step 2: In your terminal, change to the folder you just cloned:

```bash
cd sfm
```

Step 3: Run the install script:

```bash
chmod +x install.sh && ./install.sh
```

Then restart your terminal (or type `source ~/.zshrc`).

After that, you're done! You can go on to Usage!

**Windows:**

After cloning the repository locally, double-click `install.bat` or run it from Command Prompt.

After that, you can proceed to using SFM!

## Usage

After you've followed the above steps, SFM should be ready for use. (Yay!) Here's how to use it:

Open up your Terminal again and just type `sfm`.
The interactive SFM main menu should open.

If it doesn't, try fully quitting and reopening your terminal. If that fails, re-run the install script and restart your OS. If nothing else works, feel free to contact @zsharpminor on the Hack Club Slack or ask your LLM of choice!

You can pick from five options:

1. **Remove Background** — removes the background from any image locally (no uploads, ever)
2. **Convert** — converts images, audio, video, and documents to any common format
3. **Transcribe** — transcribes audio or video to text via the free Groq Whisper API
4. **Compress** — compresses images, video, and audio with simple presets
5. **Make Readable** — strips ads, paywalls, and noise from any URL

You can also skip the menu entirely — just paste a file path directly into the prompt and SFM will auto-route it to the right action. Paste a URL and it goes straight to Make Readable.

**Note**: The API key for Trancribe is hard-coded, and has a daily limit of about 480 minutes. If your files exceed this limit, please register your own API key at https://console.groq.com/ for free! I intentionally hardcoded the API since it's free and there's no payment information linked to the account, so don't even try.

By default, converted and compressed files are saved to the same folder as the source file. Background-removed images are saved as `filename_nobg.png` alongside the original.

Made with ♡ by zsharpminor, in equivocal hate of the complexity of conventional file conversion tools!