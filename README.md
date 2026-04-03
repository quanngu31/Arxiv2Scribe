# Arxiv2Scribe

Arxiv2Scribe is a simple script that converts LaTeX source (downloaded from Arxiv) and recompiles it to better fit the **Kindle Scribe**.

You may change the width and heith settings to better fit your device. However, the code shipped with default settings tailored to the Kindle Scribe (specifically the 2024 version.)

**Notes:** This is a fork from [Arxiv2Kindle](https://github.com/soumik12345/Arxiv2Kindle).

## Usage

Install the dependencies using `uv sync`.

Arxiv2Scribe can be used via a CLI:

```
uv run arxiv2scribe.py --help

Usage: arxiv2scribe.py [OPTIONS]

╭─ Options ────────────────────────────────────────────────────────────────────────────╮
│ *  --arxiv-url           -u      TEXT   arXiv paper URL [required]                   │
│    --width               -w      FLOAT  Paper width in inches [default: 5.25]        │
│    --height              -h      FLOAT  Paper height in inches [default: 7]          │
│    --margin              -m      FLOAT  Margin in inches (0–1) [default: 0.45]       │
│    --help                               Show this message and exit.                  │
╰──────────────────────────────────────────────────────────────────────────────────────╯
```
