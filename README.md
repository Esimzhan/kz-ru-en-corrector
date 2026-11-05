# Gemini Corrector

A small Windows tray app that fixes typos, punctuation and light grammar in any text box with one hotkey. It is built for people who type fast in **English, Russian and Kazakh**, often mixed in one message, and it keeps your own words, style and language (it never translates).

It uses Google's Gemini API, with an optional **local model** (Gemma 4 E4B via [Ollama](https://ollama.com)) as a fast backup when Gemini is slow or offline.

## Hotkeys

| Hotkey | What it does |
|---|---|
| `Ctrl` + `A` + `A` (hold Ctrl, tap A twice) | Selects all text in the current box and fixes it |
| `Ctrl` + `Alt` + `Z` | Fixes only the selected text |
| Select text starting with `\` | Sends it to Gemini as a question and replaces it with the answer (e.g. `\translate to russian: hello`) |

The tray icon shows the status: blue = ready, yellow = working, green = done, red = error (hover for the message). Right-click → *Open log* shows which model answered and how long it took.

## How it picks a model

1. Gemini (`gemini-3.5-flash-lite` first) gets the text.
2. If Gemini hasn't answered after **0.75 s**, the local model starts too, and whichever answers first wins. If Gemini wins, the local request is cancelled.
3. Busy (503), rate-limited (429) or hung Gemini models are retried or skipped automatically; a model that is out of quota is skipped until Google says it may be retried.
4. Ollama is started (hidden) only when it is first needed, and the model leaves GPU memory after 1 hour without use.

Typical times: 0.6–1.5 s with Gemini, about 1.5–2.5 s with the local model once it is loaded (the first load takes ~15 s).

## Setup

**Requirements:** Windows 10/11, Python 3.13+, a free [Gemini API key](https://aistudio.google.com/apikey).

1. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Store your API key as a user environment variable (never put it in the code):
   ```bash
   setx GEMINI_API_KEY "your-key-here"
   ```
   Open a new terminal (or sign out and back in) so the app can see it.
3. *(Optional, recommended)* Install the local backup model. Install [Ollama](https://ollama.com/download), then:
   ```bash
   ollama pull gemma4:e4b
   ```
   It needs about 6.6 GB of disk and runs fully on a 4 GB NVIDIA GPU. Without it, the app simply uses Gemini only. To turn it off, set `LOCAL_MODEL = None` in `app.py`.
4. Run it:
   ```bash
   pythonw app.py
   ```
   The tray icon appears after a 10-second delay (so it also works when started at boot).
5. *(Optional)* Start it with Windows: press `Win + R`, type `shell:startup`, and put a shortcut there to `pythonw.exe "C:\path\to\app.py"`.

## Linux (X11)

`app_linux.py` is the same app for Linux desktops running X11 (not Wayland): same models, prompt and hotkeys. Tested on Ubuntu 22.04 with GNOME.

1. Install the system packages and the Python dependencies:
   ```bash
   sudo apt install xclip gir1.2-ayatanaappindicator3-0.1
   python3 -m venv --system-site-packages .venv   # system packages give the tray icon access to GTK
   .venv/bin/pip install pyperclip pystray pillow python-xlib
   ```
2. Put your API key in `~/.config/gemini-corrector/api_key` (`chmod 600` it), or set `GEMINI_API_KEY`.
3. Start it at login with a systemd user service (`~/.config/systemd/user/gemini-corrector.service`):
   ```ini
   [Unit]
   PartOf=graphical-session.target
   After=graphical-session.target

   [Service]
   ExecStart=/path/to/.venv/bin/python /path/to/app_linux.py
   Restart=on-failure
   RestartSec=5

   [Install]
   WantedBy=graphical-session.target
   ```
   then `systemctl --user enable --now gemini-corrector`.

Differences from Windows: errors appear as desktop notifications, the log is in `~/.cache/gemini-corrector/`, `Ctrl+Alt+Z` also reaches the focused app (it isn't swallowed), and the hotkeys don't work in terminals, where `Ctrl+C` interrupts instead of copying. Ollama is used if `ollama` is installed; otherwise the app uses Gemini only.

The separate [Codex Screen Answer](codex-screen-answer/README.md) app runs in
the background: press Alt+C to send the whole screen and the same knowledge
files to Codex, then paste its short answer with Ctrl+V.

### Short answers and Markdown references (Linux)

Hold **Ctrl**, tap **A**, then **S** within 0.4 seconds. The app selects all text in
the current editable field and replaces the question with a short answer. For a
test, it requests the correct option letter and full answer text (for example,
`1. B. There is no effect.`), without explanations, keeping question numbers for
multiple questions. Calculations are checked against the reference definitions
before choosing an option. Other answers are limited by the prompt to 1–3
short sentences. Ordinary Ctrl+S still saves; S is captured only during this sequence.

Put your UTF-8 `.md` files directly inside **`knowledge/`**, next to `app_linux.py`.
You can open it from the tray menu → **Open reference folder**. All Markdown files
are reloaded for every question, so additions and edits need no restart. Personal
reference files are ignored by Git. Subfolders and symbolic links are not loaded.

Both Ctrl+A+S and the existing `\question` mode receive these references. When
nonempty files are present, the model is instructed to answer only from them,
and to say when information is missing or conflicting. With no reference content,
it uses general knowledge. Spelling correction does not use the files. Short-answer
formatting applies only to Ctrl+A+S. Model answers can still be wrong.

The question and full reference content are sent to Gemini with each answer
request. The combined Markdown limit is 512 KB; oversized or unreadable files
produce an error instead of silently dropping context. Answer mode uses Gemini,
without the small local spelling model.

## Settings

All settings are at the top of `app.py`:

| Setting | Default | Meaning |
|---|---|---|
| `MODELS` | 5 Gemini models | Gemini models to try, in order |
| `LOCAL_MODEL` | `"gemma4:e4b"` | Local Ollama model, or `None` to use Gemini only |
| `GEMINI_FIRST_SECONDS` | `0.75` | How long Gemini gets before the local model joins |
| `LOCAL_KEEP_ALIVE` | `"1h"` | How long the local model stays in GPU memory after use |
| `LOG_TEXT` | `False` | Also log your text and the fixes (debugging only) |
| `CORRECTION_PROMPT` | | The instructions sent with every fix |

## Privacy

- **Your text is sent to Google** whenever Gemini is used. On the free tier of the Gemini API, Google may use what you send to improve its products; see [Google's Gemini API terms](https://ai.google.dev/gemini-api/terms). Don't use the tool on passwords or text you can't share, or set `MODELS = []` with a local model to keep everything on your PC.
- **The local model runs entirely on your PC.** Ollama listens only on `127.0.0.1`.
- **The API key** is read from the `GEMINI_API_KEY` environment variable and sent only to Google, in a request header over HTTPS. It is never logged.
- **The log** (`%TEMP%\gemini_corrector_debug.log`) records timings, model names and errors, but **not your text** unless you turn on `LOG_TEXT`. It is rotated at 1 MB.
- **Clipboard:** the app uses the clipboard to copy and paste, then restores what you had before. If Windows clipboard history (`Win + V`) is on, the copied text may appear there.
- **Local files stay local:** API key files, `.env` files, virtual environments,
  logs, screenshots and all Markdown files under `knowledge/` are ignored by Git.
  The tracked `.gitkeep` only preserves an empty knowledge folder. Check
  `git status` before committing any new file that may contain personal data.

## Building an .exe

```bash
pip install pyinstaller
pyinstaller --onefile --noconsole --name "GeminiCorrector" app.py
```

The file is created in `dist\GeminiCorrector.exe`. The API key still comes from the environment variable, not from the .exe.

## License

[MIT](LICENSE)
