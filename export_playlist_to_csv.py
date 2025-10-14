#!/usr/bin/env python3
import argparse
import csv
import os
import re
from typing import Iterable, List, Optional, Tuple

from dotenv import load_dotenv
from unidecode import unidecode
import spotipy
from spotipy.oauth2 import SpotifyOAuth

SCOPES = ["playlist-read-private", "playlist-read-collaborative"]

def norm(s: str) -> str:
    return unidecode((s or "").strip())

def artists_str(artists: List[dict]) -> str:
    return ", ".join(norm(a.get("name","")) for a in (artists or []) if a and a.get("name"))

def parse_args():
    ap = argparse.ArgumentParser(description="Export a Spotify playlist you can access to CSV.")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--playlist", help="Playlist URL/URI/ID to export.")
    src.add_argument("--name", help="Playlist name to pick (best match among your playlists).")

    ap.add_argument("--out", default="playlist_tracks.csv", help="Output CSV path (default: playlist_tracks.csv)")
    ap.add_argument("--market", default=None, help="Market code (e.g., GB, US) for track metadata bias.")
    ap.add_argument("--include-local", action="store_true", help="Include local/unavailable tracks (off by default).")
    return ap.parse_args()

def extract_playlist_id(s: str) -> str:
    s = s.strip()
    # Support URL, URI, or raw ID
    m = re.search(r"(?:open\.spotify\.com/playlist/|spotify:playlist:)([A-Za-z0-9]{22})", s)
    if m:
        return m.group(1)
    # if looks like an ID
    if re.fullmatch(r"[A-Za-z0-9]{22}", s):
        return s
    return s  # let API error if malformed

def find_playlist_by_name(sp: spotipy.Spotify, user_id: str, target: str) -> Optional[dict]:
    target_n = norm(target).lower()
    best = None
    best_score = -1

    limit = 50
    offset = 0
    while True:
        page = sp.current_user_playlists(limit=limit, offset=offset)
        items = page.get("items", []) or []
        for pl in items:
            name = norm(pl.get("name",""))
            score = 0
            if name.lower() == target_n:
                score = 100
            elif target_n in name.lower():
                score = 80 - abs(len(name) - len(target))
            else:
                # simple overlap score
                t_words = set(target_n.split())
                n_words = set(name.lower().split())
                score = len(t_words & n_words)
            if score > best_score:
                best_score = score
                best = pl
        if not page.get("next"):
            break
        offset += limit
    return best

def iter_playlist_tracks(sp: spotipy.Spotify, playlist_id: str, market: Optional[str], include_local: bool):
    """
    Yield rows (position,title,artists,album,added_at,duration_ms,isrc,spotify_url)
    """
    limit = 100
    offset = 0
    pos = 0
    while True:
        page = sp.playlist_items(
            playlist_id,
            market=market,
            limit=limit,
            offset=offset,
            additional_types=("track",),
            fields="items(added_at,track(is_local,available_markets,name,uri,external_urls.spotify,"
                   "duration_ms,external_ids.isrc,artists(name),album(name))),next"
        )
        items = page.get("items", []) or []
        for it in items:
            tr = it.get("track")
            if not tr:
                continue
            is_local = tr.get("is_local", False)
            if is_local and not include_local:
                continue
            title = norm(tr.get("name",""))
            artists = artists_str(tr.get("artists", []))
            album = norm((tr.get("album") or {}).get("name",""))
            url = (tr.get("external_urls") or {}).get("spotify","")
            isrc = ((tr.get("external_ids") or {}).get("isrc") or "").strip()
            duration_ms = tr.get("duration_ms", 0)
            added_at = it.get("added_at","")

            pos += 1
            yield (pos, title, artists, album, added_at, duration_ms, isrc, url)
        if not page.get("next"):
            break
        offset += limit

def main():
    load_dotenv()  # SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI
    args = parse_args()

    auth = SpotifyOAuth(scope=" ".join(SCOPES))
    sp = spotipy.Spotify(auth_manager=auth)

    me = sp.me()
    user_id = me["id"]

    if args.playlist:
        playlist_id = extract_playlist_id(args.playlist)
        pl = sp.playlist(playlist_id, fields="name,id")
    else:
        pl = find_playlist_by_name(sp, user_id, args.name)
        if not pl:
            raise SystemExit(f"Could not find a playlist matching name: {args.name!r}")
        playlist_id = pl["id"]

    pl_name = pl.get("name","")
    rows = list(iter_playlist_tracks(sp, playlist_id, args.market, args.include_local))

    # Deduplicate exact duplicates by (title, artists, album, url)
    seen = set()
    deduped = []
    for (position, title, artists, album, added_at, duration_ms, isrc, url) in rows:
        key = (title, artists, album, url)
        if key not in seen:
            seen.add(key)
            deduped.append((position, title, artists, album, added_at, duration_ms, isrc, url))

    out_path = args.out
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["position","title","artists","album","added_at","duration_ms","isrc","spotify_url","playlist_name","playlist_id"])
        for (position, title, artists, album, added_at, duration_ms, isrc, url) in deduped:
            w.writerow([position, title, artists, album, added_at, duration_ms, isrc, url, pl_name, playlist_id])

    print(f"Wrote {len(deduped)} tracks to {out_path}")

if __name__ == "__main__":
    main()
