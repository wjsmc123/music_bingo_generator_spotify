# 🎵 Spotify Playlist → CSV → Music Bingo Generator

This project automates everything from exporting your **Spotify playlists** to printable **4×4 music bingo cards (PDF)**

---

## 🚀 Features

Export any playlist from your **Spotify account** (including private and collaborative ones).  
Save track details (title, artist, album, etc.) into a **CSV file**.  
Automatically create **X number of 4×4 bingo cards**, each filled with random songs from that playlist.  
Generates a **multi-page PDF**, ready to print.  
Optional **titles**, **subtitles**, and **no-repeat** settings for unique cards.  
Simple interactive runner — no arguments needed if you don’t want to type commands.

---

## Project Structure

```
spotify_playlist_export/
├── main.py                  ← Main runner (end-to-end pipeline)
│
├── export_playlist_to_csv.py         ← Exports Spotify playlist to CSV
│
├── make_bingo_from_csv.py            ← Generates 4×4 bingo cards from CSV
│
├── README_bingo.md
├── .env                                  ← Spotify API credentials
└── requirements.txt                      ← Dependencies
```

---

## Step-by-step Setup

### 1. Install Dependencies
Use **Python 3.13** (recommended).

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Set Up Spotify Developer Credentials
1. Go to **[Spotify Developer Dashboard](https://developer.spotify.com/dashboard/)**  
2. Create a new app and add the Redirect URI:
   ```
   http://127.0.0.1:8080/callback
   ```
   ⚠️ Spotify no longer accepts `localhost` — you must use `127.0.0.1`.
3. Copy your **Client ID** and **Client Secret** into the `.env` file:

   ```
   SPOTIPY_CLIENT_ID=your_client_id
   SPOTIPY_CLIENT_SECRET=your_client_secret
   SPOTIPY_REDIRECT_URI=http://127.0.0.1:8080/callback
   ```

---

## 🎯 How to Run the Full Pipeline

Once your credentials are ready, run:
```bash
python main.py
```

The script will guide you interactively:

1. **Enter the playlist name** (must exist in your Spotify account)  
2. **Choose market code** (e.g. `GB`, `US`)  
3. It will export your playlist to a CSV (e.g. `My_Playlist.csv`)  
4. Then it will ask:  
   - How many bingo cards to generate  
   - Title / subtitle for each card  
   - Whether to avoid repeating songs across cards
5. Finally, it generates a multi-page PDF (e.g. `My_Playlist_bingo.pdf`)

---

## Output Examples

### CSV (Exported)
| title | artists | album |
|--------|----------|--------|
| Mr. Brightside | The Killers | Hot Fuss |
| Toxic | Britney Spears | In the Zone |
| Jolene | Dolly Parton | Jolene |

### Bingo PDF
Each page contains a 4×4 grid like this:

```
┌────────────────────────────┬──────────────────────────┬──────────────────────────┬────────────────────────────┐
│ Mr. Brightside — The Killers │ Toxic — Britney Spears │ Jolene — Dolly Parton │ Do I Wanna Know? — Arctic Monkeys │
│ ...                         │ ...                    │ ...                    │ ...                         │
└────────────────────────────┴──────────────────────────┴──────────────────────────┴────────────────────────────┘
```

Each card uses a random subset of your playlist songs.

---

## Advanced Options

You can also call the sub-scripts directly.

### Export only:
```bash
python spotify_playlist_export/export_playlist_to_csv.py --name "My Playlist" --out songs.csv --market GB
```

### Generate bingo cards manually:
```bash
python spotify_bingo/make_bingo_from_csv.py --csv songs.csv --n 6 --out bingo.pdf --title "Friday Music Bingo" --no-repeat-across --seed 42
```

**Flags:**
| Flag | Description |
|------|--------------|
| `--csv` | Input CSV file (must contain `title` and `artists`) |
| `--n` | Number of bingo cards to generate |
| `--out` | Output PDF filename |
| `--no-repeat-across` | Prevent reusing the same song across different cards |
| `--seed` | Random seed for reproducible grids |
| `--title` / `--subtitle` | Optional header text on each card |

---

## Troubleshooting

**Problem:** Spotify won’t let you use `http://localhost` redirect URI.  
**Fix:** Use `http://127.0.0.1:8080/callback` — Spotify now disallows `localhost`.

**Problem:** Title/subtitle not appearing in PDF.  
**Fix:** Ensure your `draw_card()` function doesn’t clear the figure (`remove fig.clf()`).

**Problem:** Empty cards or missing data.  
**Fix:** Make sure your CSV has `title` and `artists` columns exactly spelled.

---

## Credits

- [Spotipy](https://spotipy.readthedocs.io/) — Spotify Web API Python client.  
- [Matplotlib](https://matplotlib.org/) — for rendering printable bingo cards.  
- Project designed and structured by **Will Mansell-Cook**   

Enjoy your music bingo nights! 
