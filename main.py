
#!/usr/bin/env python3
import os
import sys
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent

EXPORT_SCRIPT = HERE / "export_playlist_to_csv.py"
BINGO_SCRIPT = HERE / "make_bingo_from_csv.py"

def require_file(path: Path, desc: str):
    if not path.exists():
        print(f"❌ Missing {desc}: {path}")
        print("   Make sure you've downloaded the project files so this runner can call them.")
        sys.exit(1)

def ask(prompt: str, default: str = "") -> str:
    s = input(f"{prompt}{' ['+default+']' if default else ''}: ").strip()
    return s or default

def to_filename(name: str, ext: str) -> str:
    base = "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in name.strip())
    base = base.strip("_") or "output"
    if not base.lower().endswith(f".{ext.lower()}"):
        base += f".{ext}"
    return base

def main():
    print("🎵 Spotify Playlist → Music Bingo (PDF)")
    print("=================================================")
    require_file(EXPORT_SCRIPT, "export script")
    require_file(BINGO_SCRIPT, "bingo script")

    # --- Ask for playlist and export CSV
    playlist_name = ask("Enter the name of the Spotify playlist you want to export")
    if not playlist_name:
        print("❌ No playlist name entered. Exiting.")
        sys.exit(1)

    market = ask("Market code (e.g., GB, US)", "GB")
    csv_out = "csv_files/" + to_filename(playlist_name.replace(" ", "_"), "csv")

    print(f"\n▶️  Exporting playlist '{playlist_name}' to {csv_out} ...\n")
    try:
        subprocess.run([
            sys.executable, str(EXPORT_SCRIPT),
            "--name", playlist_name,
            "--out", csv_out,
            "--market", market
        ], check=True)
    except subprocess.CalledProcessError as e:
        print("\n❌ Export failed. Please check your Spotify credentials and scopes.")
        sys.exit(e.returncode)

    print(f"\n✅ Export complete: {csv_out}")

    # --- Ask for bingo settings
    print("\n🧩 Bingo card settings")
    try:
        n_cards = int(ask("How many 4x4 bingo cards to generate", "6"))
    except ValueError:
        print("❌ Invalid number. Exiting.")
        sys.exit(1)

    title = ask("Title to display on each card (optional)", f"Music Bingo — {playlist_name}")
    subtitle = ask("Subtitle (optional)", "")

    # options
    no_repeat_across = ask("Avoid reusing the same song across different cards? (y/N)", "N").lower().startswith("y")

    pdf_out = "quiz_pdfs/" + to_filename(f"{playlist_name.replace(' ', '_')}_bingo", "pdf")

    # --- Build bingo command
    cmd = [
        sys.executable, str(BINGO_SCRIPT),
        "--csv", csv_out,
        "--n", str(n_cards),
        "--out", pdf_out
    ]
    if title:
        cmd += ["--title", title]
    if subtitle:
        cmd += ["--subtitle", subtitle]
    if no_repeat_across:
        cmd += ["--no-repeat-across"]

    print(f"\n🖨️  Generating bingo PDF: {pdf_out} ...\n")
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print("\n❌ Bingo generation failed. Ensure matplotlib is installed and CSV has 'title' and 'artists' columns.")
        sys.exit(e.returncode)

    print(f"\n✅ All done!\n- CSV: {csv_out}\n- Bingo PDF: {pdf_out}\n")

if __name__ == "__main__":
    main()
