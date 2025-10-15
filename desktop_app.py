#!/usr/bin/env python3
"""
Minimal Tkinter desktop app that wraps the existing CLI runner functionality.

It collects playlist name, market, number of cards, title/subtitle, and a "no repeat across" option,
then runs the two existing scripts (`export_playlist_to_csv.py` and `make_bingo_from_csv.py`) using
the same arguments. Execution runs in a background thread and logs are shown in the GUI.

Run: python desktop_app.py
"""

import threading
import subprocess
import sys
from pathlib import Path
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

HERE = Path(__file__).resolve().parent
EXPORT_SCRIPT = HERE / "export_playlist_to_csv.py"
BINGO_SCRIPT = HERE / "make_bingo_from_csv.py"


def to_filename(name: str, ext: str) -> str:
    base = "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in name.strip())
    base = base.strip("_") or "output"
    if not base.lower().endswith(f".{ext.lower()}"):
        base += f".{ext}"
    return base


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Music Bingo — Desktop")
        self.geometry("640x520")

        frm = ttk.Frame(self, padding=12)
        frm.pack(fill=tk.BOTH, expand=True)

        # Playlist name
        ttk.Label(frm, text="Spotify playlist name:").grid(row=0, column=0, sticky=tk.W)
        self.playlist_var = tk.StringVar()
        ttk.Entry(frm, textvariable=self.playlist_var, width=50).grid(row=0, column=1, columnspan=3, sticky=tk.W)

        # Market
        ttk.Label(frm, text="Market (GB/US):").grid(row=1, column=0, sticky=tk.W)
        self.market_var = tk.StringVar(value="GB")
        ttk.Entry(frm, textvariable=self.market_var, width=10).grid(row=1, column=1, sticky=tk.W)

        # Number of cards
        ttk.Label(frm, text="# of 4x4 cards:").grid(row=2, column=0, sticky=tk.W)
        self.n_var = tk.IntVar(value=6)
        ttk.Spinbox(frm, from_=1, to=200, textvariable=self.n_var, width=6).grid(row=2, column=1, sticky=tk.W)

        # Title / subtitle
        ttk.Label(frm, text="Card title (optional):").grid(row=3, column=0, sticky=tk.W)
        self.title_var = tk.StringVar()
        ttk.Entry(frm, textvariable=self.title_var, width=50).grid(row=3, column=1, columnspan=3, sticky=tk.W)

        ttk.Label(frm, text="Subtitle (optional):").grid(row=4, column=0, sticky=tk.W)
        self.subtitle_var = tk.StringVar()
        ttk.Entry(frm, textvariable=self.subtitle_var, width=50).grid(row=4, column=1, columnspan=3, sticky=tk.W)

        # No repeat across
        self.no_repeat_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(frm, text="Avoid reusing same song across different cards", variable=self.no_repeat_var).grid(row=5, column=0, columnspan=4, sticky=tk.W)

        # Output display paths
        ttk.Label(frm, text="CSV output path:").grid(row=6, column=0, sticky=tk.W)
        self.csv_out_var = tk.StringVar(value="csv_files/playlist_tracks.csv")
        ttk.Entry(frm, textvariable=self.csv_out_var, width=50).grid(row=6, column=1, columnspan=3, sticky=tk.W)

        ttk.Label(frm, text="PDF output path:").grid(row=7, column=0, sticky=tk.W)
        self.pdf_out_var = tk.StringVar(value="quiz_pdfs/bingo_cards.pdf")
        ttk.Entry(frm, textvariable=self.pdf_out_var, width=50).grid(row=7, column=1, columnspan=3, sticky=tk.W)

        # Buttons
        self.run_btn = ttk.Button(frm, text="Run", command=self.on_run)
        self.run_btn.grid(row=8, column=1, sticky=tk.W, pady=8)
        ttk.Button(frm, text="Quit", command=self.destroy).grid(row=8, column=2, sticky=tk.W)

        # Log window
        ttk.Label(frm, text="Log:").grid(row=9, column=0, sticky=tk.W)
        self.log = scrolledtext.ScrolledText(frm, height=12, wrap=tk.WORD)
        self.log.grid(row=10, column=0, columnspan=4, sticky=tk.NSEW)

        frm.rowconfigure(10, weight=1)
        frm.columnconfigure(3, weight=1)

    def log_msg(self, s: str):
        self.log.insert(tk.END, s + "\n")
        self.log.see(tk.END)

    def on_run(self):
        playlist = self.playlist_var.get().strip()
        if not playlist:
            messagebox.showerror("Missing playlist", "Please enter a playlist name or URL.")
            return

        # compute filenames
        csv_out = self.csv_out_var.get().strip() or f"csv_files/{to_filename(playlist.replace(' ', '_'), 'csv')}"
        pdf_out = self.pdf_out_var.get().strip() or f"quiz_pdfs/{to_filename(playlist.replace(' ', '_') + '_bingo', 'pdf')}"

        # disable run button while running
        self.run_btn.config(state=tk.DISABLED)
        self.log_msg(f"Starting export for '{playlist}' -> {csv_out}")

        thread = threading.Thread(target=self.run_pipeline, args=(playlist, csv_out, pdf_out), daemon=True)
        thread.start()

    def run_pipeline(self, playlist: str, csv_out: str, pdf_out: str):
        try:
            # Run export script
            cmd1 = [sys.executable, str(EXPORT_SCRIPT), "--name", playlist, "--out", csv_out, "--market", self.market_var.get().strip() or "GB"]
            self.log_msg("Running: " + " ".join(cmd1))
            p1 = subprocess.run(cmd1, capture_output=True, text=True)
            self.log_msg(p1.stdout.strip())
            if p1.returncode != 0:
                self.log_msg(p1.stderr.strip())
                messagebox.showerror("Export failed", "Export script failed. See logs.")
                return
            self.log_msg(f"Export complete: {csv_out}")

            # Run bingo script
            cmd2 = [sys.executable, str(BINGO_SCRIPT), "--csv", csv_out, "--n", str(self.n_var.get()), "--out", pdf_out]
            if self.title_var.get().strip():
                cmd2 += ["--title", self.title_var.get().strip()]
            if self.subtitle_var.get().strip():
                cmd2 += ["--subtitle", self.subtitle_var.get().strip()]
            if self.no_repeat_var.get():
                cmd2 += ["--no-repeat-across"]

            self.log_msg("Running: " + " ".join(cmd2))
            p2 = subprocess.run(cmd2, capture_output=True, text=True)
            self.log_msg(p2.stdout.strip())
            if p2.returncode != 0:
                self.log_msg(p2.stderr.strip())
                messagebox.showerror("Bingo generation failed", "Bingo script failed. See logs.")
                return
            self.log_msg(f"Bingo complete: {pdf_out}")
            messagebox.showinfo("Done", f"Exported CSV: {csv_out}\nBingo PDF: {pdf_out}")
        except Exception as e:
            self.log_msg(f"Error: {e}")
            messagebox.showerror("Error", str(e))
        finally:
            self.run_btn.config(state=tk.NORMAL)


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
