# Codex Screen Answer

On an X11 desktop, press **Alt+C** to capture the whole screen and ask Codex
to answer the visible question(s). Nothing opens on screen. When it finishes,
paste the answer with **Ctrl+V**. For a test, the answer includes the choice
letter and full text without an explanation.

The app uses `gpt-6-sol` through the signed-in Codex CLI. To use Terra instead,
change `MODEL` near the top of `app.py` to `gpt-5.6-terra` and restart the user
service. The same Markdown files as Gemini Corrector are read on each request
from `~/apps/kz-ru-en-corrector/knowledge/`. These files and a screenshot of
the entire desktop are sent to Codex when you press Alt+C. Screenshots and
answers are held only in a private temporary folder and removed after the
request. On failure, the previous clipboard contents remain. The app logs only
status and errors to `~/.cache/codex-screen-answer/app.log`.

The app requires X11, `codex` already signed in, `xclip`, Pillow, and
`python-xlib`. On Ubuntu, install `xclip` and `python3-venv`, then create a
virtual environment in this directory and install `pillow python-xlib` into it.
Copy `codex-screen-answer.service` to `~/.config/systemd/user/`, adjust its
paths if you cloned elsewhere, then run `systemctl --user daemon-reload` and
`systemctl --user enable --now codex-screen-answer.service`.
On this PC, it is installed as that systemd user service and starts with the
graphical session. Check it with `systemctl --user status codex-screen-answer`.

The model can make mistakes. If the answer is missing after a while, check the
log for an error. The Codex CLI is run with a read-only sandbox and ephemeral
session. No text is pasted automatically.
