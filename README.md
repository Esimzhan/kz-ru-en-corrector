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

## Building an .exe

```bash
pip install pyinstaller
pyinstaller --onefile --noconsole --name "GeminiCorrector" app.py
```

The file is created in `dist\GeminiCorrector.exe`. The API key still comes from the environment variable, not from the .exe.
