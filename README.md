# Arxiv2Kindle

Arxiv2Kindle is a simple script written in python that converts LaTeX source downloaded from Arxiv and recompiles it to better fit a reading device (such as a Kindle).

<!--## Features

- Arxiv2Kindle can render images, diagrams, tables and formulae.
- It also converts 2-column formats into a single column for ease of reading.
- Arxiv2Kindle can mail the converted pdf file to your kindle (if you have a wifi-enabled Kindle).

**Note:**

- Arxiv2Kindle does not work on papers without the source.
- The fixed transformations applied on the source may not lead to a desired result in a few cases. Still, on most cases the results are readable.-->

## Usage

Install the dependencies using `uv sync`.

Arxiv2Kindle can be used via a CLI:

```
uv run arxiv2kindle.py --help

Usage: arxiv2kindle.py [OPTIONS]

╭─ Options ────────────────────────────────────────────────────────────────────────────╮
│ *  --arxiv-url           -u      TEXT   arXiv paper URL [required]                   │
│    --width               -w      FLOAT  Paper width in inches [default: 5.25]        │
│    --height              -h      FLOAT  Paper height in inches [default: 7]          │
│    --margin              -m      FLOAT  Margin in inches (0–1) [default: 0.45]       │
│    --help                               Show this message and exit.                  │
╰──────────────────────────────────────────────────────────────────────────────────────╯
```
