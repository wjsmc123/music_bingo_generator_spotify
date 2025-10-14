
#!/usr/bin/env python3
"""
Generate X 4x4 music bingo cards (PDF) from a CSV of songs exported by the Spotify script.

Input CSV must have at least columns:
  - title
  - artists
(Other columns are ignored.)

Usage:
  python make_bingo_from_csv.py --csv songs.csv --n 6 --out bingo_cards.pdf --title "Friday Night Music Bingo"

Options:
  --seed 123              Reproducible shuffles
  --no-repeat-across      Avoid reusing the same song across different cards (requires enough unique rows)
  --allow-short <int>     Allow duplicates across cards if not enough unique songs; min pool size fallback (default: 16)
  --title "..."           Title to display on each card (optional)
  --subtitle "..."        Subtitle (optional)
"""

import argparse
import csv
import random
import sys
from typing import List, Tuple
import textwrap

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

def read_songs(csv_path: str) -> List[Tuple[str, str]]:
    songs = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        cols = {c.lower(): c for c in reader.fieldnames or []}
        title_col = cols.get("title") or cols.get("track") or cols.get("name")
        artist_col = cols.get("artists") or cols.get("artist")
        if not title_col or not artist_col:
            raise SystemExit("CSV must contain columns named 'title' and 'artists'.")
        for row in reader:
            t = (row.get(title_col) or "").strip()
            a = (row.get(artist_col) or "").strip()
            if t and a:
                songs.append((t, a))
    # Deduplicate exact title+artist
    uniq = []
    seen = set()
    for t, a in songs:
        key = (t.lower(), a.lower())
        if key not in seen:
            uniq.append((t, a))
            seen.add(key)
    return uniq

def pick_card_songs(pool: List[Tuple[str,str]], k: int, used: set, no_repeat_across: bool) -> List[Tuple[str,str]]:
    available = [s for s in pool if (not no_repeat_across) or (s not in used)]
    if len(available) >= k:
        picks = random.sample(available, k)
    else:
        # Not enough unique; fill with random choices from full pool (may repeat across cards)
        picks = available[:] + random.sample(pool, k - len(available))
    if no_repeat_across:
        for s in picks:
            used.add(s)
    return picks

def wrap_label(text: str, width: int = 18) -> str:
    lines = textwrap.wrap(text, width=width)
    return "\n".join(lines)

def draw_card(fig, items: List[str]):
    # fig.clf() -- clears figure
    # Title and margin layout
    LEFT = 0.05
    RIGHT = 0.95
    TOP = 0.88
    BOTTOM = 0.06

    ax = fig.add_axes([0,0,1,1])
    ax.axis("off")

    # Draw 4x4 grid
    rows, cols = 4, 4
    cell_w = (RIGHT - LEFT) / cols
    cell_h = (TOP - BOTTOM) / rows

    for r in range(rows):
        for c in range(cols):
            x0 = LEFT + c * cell_w
            y0 = TOP - (r + 1) * cell_h
            # Rectangle
            rect = plt.Rectangle((x0, y0), cell_w, cell_h, fill=False, linewidth=1.5)
            ax.add_patch(rect)
            # Text
            idx = r * cols + c
            label = items[idx]
            ax.text(x0 + cell_w/2, y0 + cell_h/2, wrap_label(label, width=18),
                    ha='center', va='center', fontsize=9)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True, help="Input CSV with 'title' and 'artists' columns")
    ap.add_argument("--n", type=int, required=True, help="Number of bingo cards to generate")
    ap.add_argument("--out", default="bingo_cards.pdf", help="Output PDF path")
    ap.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    ap.add_argument("--no-repeat-across", action="store_true", help="Do not reuse the same song across different cards")
    ap.add_argument("--allow-short", type=int, default=16, help="If unique pool < this, allow repeats across cards (default 16)")
    ap.add_argument("--title", default=None, help="Optional title to print on each card")
    ap.add_argument("--subtitle", default=None, help="Optional subtitle to print on each card")
    args = ap.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    songs = read_songs(args.csv)
    if len(songs) < 16 and args.no_repeat_across:
        print("Not enough unique songs for one 4x4 card without repeats. Consider removing --no-repeat-across or adding more songs.", file=sys.stderr)

    used = set()
    with PdfPages(args.out) as pdf:
        for card_idx in range(args.n):
            picks = pick_card_songs(songs, 16, used, args.no_repeat_across and len(songs) >= args.allow_short)
            labels = [f"{t} — {a}" for (t,a) in picks]

            fig = plt.figure(figsize=(8.5, 11))  # A4-ish portrait
            # Header text
            y = 0.95
            if args.title:
                fig.text(0.5, y, args.title, ha='center', va='center', fontsize=16)
                y -= 0.03
            fig.text(0.5, y, f"Bingo Card #{card_idx+1}", ha='center', va='center', fontsize=12)
            if args.subtitle:
                y -= 0.03
                fig.text(0.5, y, args.subtitle, ha='center', va='center', fontsize=10)

            # Grid
            draw_card(fig, labels)

            pdf.savefig(fig)
            plt.close(fig)

    print(f"Wrote {args.n} bingo cards to {args.out}")

if __name__ == "__main__":
    main()
