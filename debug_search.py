import yt_dlp
import traceback

print("--- STARTING RAW YT-DLP SEARCH ---")

ydl_opts = {
    "quiet": False,
    "no_warnings": False,
    "skip_download": True,
    "cachedir": False,
    "ignoreerrors": True,
    # MAGIC FIX: Fetch full info for search results, but do NOT expand channels/playlists
    "extract_flat": "in_playlist", 
    "remote_components": ["ejs:github"],
    "extractor_args": {
        "youtube": {
            "player_client": ["mweb", "tv", "web_safari"],
            "fetch_pot": ["always"],
        },
        "youtubepot-bgutilhttp": {
            "base_url": ["http://127.0.0.1:4416"],
        },
    },
    "cookiesfrombrowser": ("firefox",),
}

try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        print("Fetching 'ytsearch3:laravel'...")
        info = ydl.extract_info("ytsearch3:laravel", download=False)
        
        print("\n--- SUCCESS ---")
        if info and 'entries' in info:
            for entry in info.get('entries', []):
                if entry:
                    print(f"Title: {entry.get('title')}")
                    print(f"Thumbnail: {entry.get('thumbnail')}")
            
except Exception as e:
    print("\n--- ERROR CAUGHT ---")
    traceback.print_exc()