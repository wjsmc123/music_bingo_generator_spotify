#!/usr/bin/env python3
"""
Minimal, colorful, bold Tkinter UI for Music Bingo.

This intentionally small app centers the controls, uses large bold labels,
and keeps behavior identical to the CLI runner. It runs the export and bingo
commands in a background thread so the UI stays responsive.

Run: python desktop_app.py
"""

import threading
import subprocess
import sys
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

HERE = Path(__file__).resolve().parent
EXPORT_SCRIPT = HERE / "export_playlist_to_csv.py"
BINGO_SCRIPT = HERE / "make_bingo_from_csv.py"


def to_filename(name: str, ext: str) -> str:
    base = "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in name.strip())
    base = base.strip("_") or "output"
    if not base.lower().endswith(f".{ext.lower()}"):
        base += f".{ext}"
    return base


class SimpleApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Music Bingo")
        self.geometry("640x360")
        self.configure(bg="#212121")
        self.resizable(False, False)

        self.status_var = tk.StringVar(value="Ready")

        # bold fonts and palette
        header_font = ("Helvetica", 20, "bold")
        label_font = ("Helvetica", 12, "bold")
        btn_font = ("Helvetica", 12, "bold")
        accent = "#FF5F6D"  # pink/orange feel

        container = tk.Frame(self, bg="#212121")
        container.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        tk.Label(container, text="Music Bingo Generator", fg="#1DB954", bg="#212121", font=header_font).grid(row=0, column=0, columnspan=2, pady=(0,12))

        tk.Label(container, text="Playlist:", fg="white", bg="#212121", font=label_font).grid(row=1, column=0, sticky=tk.E, padx=(0,8))
        self.playlist_var = tk.StringVar()
        tk.Entry(container, textvariable=self.playlist_var, width=40, bg="#222", fg="white", bd=0, insertbackground='white').grid(row=1, column=1, pady=6)

        tk.Label(container, text="Cards:", fg="white", bg="#212121", font=label_font).grid(row=2, column=0, sticky=tk.E, padx=(0,8))
        self.n_var = tk.IntVar(value=6)
        tk.Entry(container, textvariable=self.n_var, width=6, bd=0).grid(row=2, column=1, sticky=tk.W)

        tk.Label(container, text="Card title:", fg="white", bg="#212121", font=label_font).grid(row=3, column=0, sticky=tk.E, padx=(0,8), pady=(8,0))
        self.title_var = tk.StringVar()
        tk.Entry(container, textvariable=self.title_var, width=40, bg="#222", fg="white", bd=0).grid(row=3, column=1, pady=(8,0))

        tk.Label(container, text="No repeat:", fg="white", bg="#212121", font=label_font).grid(row=4, column=0, sticky=tk.E, padx=(0,8), pady=(8,0))
        self.no_repeat_var = tk.BooleanVar(value=False)
        tk.Checkbutton(container, variable=self.no_repeat_var, bg="#212121", fg="#535353", activebackground="#0E0E0E", highlightthickness=0).grid(row=4, column=1, sticky=tk.W, pady=(8,0))

        run_btn = tk.Button(container, text="Run", bg=accent, fg="#212121", font=btn_font, activebackground=accent, command=self.on_run, width=12, bd=0)
        run_btn.grid(row=5, column=0, columnspan=2, pady=(12,0))
        status_lbl = tk.Label(container, textvariable=self.status_var, fg="white", bg="#212121", font=label_font)
        status_lbl.grid(row=6, column=0, columnspan=2, pady=(12,0))

    def set_status(self, s: str):
        self.status_var.set(s)

    def on_run(self):
        playlist = self.playlist_var.get().strip()
        if not playlist:
            messagebox.showerror("Missing", "Please enter a playlist name or URL")
            return

        csv_out = f"csv_files/{to_filename(playlist.replace(' ', '_'), 'csv')}"
        pdf_out = f"quiz_pdfs/{to_filename(playlist.replace(' ', '_') + '_bingo', 'pdf')}"

        t = threading.Thread(target=self._work, args=(playlist, csv_out, pdf_out), daemon=True)
        t.start()

    def _work(self, playlist, csv_out, pdf_out):
        try:
            self.after(0, lambda: self.set_status("Exporting..."))
            cmd1 = [sys.executable, str(EXPORT_SCRIPT), "--name", playlist, "--out", csv_out]
            p1 = subprocess.run(cmd1, capture_output=True, text=True)
            if p1.returncode != 0:
                self.after(0, lambda: messagebox.showerror("Export failed", p1.stderr or p1.stdout))
                return
            self.after(0, lambda: self.set_status("Generating bingo PDF..."))
            cmd2 = [sys.executable, str(BINGO_SCRIPT), "--csv", csv_out, "--n", str(self.n_var.get()), "--out", pdf_out]
            if self.title_var.get().strip():
                cmd2 += ["--title", self.title_var.get().strip()]
            if self.no_repeat_var.get():
                cmd2 += ["--no-repeat-across"]
            p2 = subprocess.run(cmd2, capture_output=True, text=True)
            if p2.returncode != 0:
                self.after(0, lambda: messagebox.showerror("Bingo failed", p2.stderr or p2.stdout))
                return
            self.after(0, lambda: self.set_status("Done"))
            self.after(0, lambda: messagebox.showinfo("Done", f"COMPLETED\nPDF located at: {pdf_out}"))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally:
            self.after(0, lambda: self.set_status("Ready"))


def main():
    app = SimpleApp()
    app.mainloop()


if __name__ == "__main__":
    main()
