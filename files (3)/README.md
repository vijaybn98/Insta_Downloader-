# BJP4Karnataka YouTube Caption Monitor

Automatically watches the BJP4Karnataka YouTube channel for new videos and Shorts,
extracts captions, and appends them to a CSV — no API key required.

---

## What it captures

| Column | Description |
|---|---|
| `fetched_at` | When the row was written (UTC) |
| `published` | When YouTube published the video |
| `type` | `Video` or `Short` |
| `title` | Video title |
| `video_id` | YouTube video ID |
| `url` | Full YouTube link |
| `lang_used` | Caption language code (`kn`, `hi`, `en`, etc.) |
| `caption` | Full caption/transcript text |

---

## Setup (one-time)

### 1. Find the Channel ID

The Channel ID is **not** the same as the handle (`@bjp4karnataka`).

**Easy way:**
1. Go to `https://www.youtube.com/@bjp4karnataka`
2. Right-click → View Page Source
3. Search for `"channelId"` → copy the value (e.g. `UCkBExJoIu47kqk8GXNj4ZYw`)

Or use this URL to confirm it works:
```
https://www.youtube.com/feeds/videos.xml?channel_id=YOUR_CHANNEL_ID
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set the Channel ID

Either edit `monitor.py` and replace `CHANNEL_ID` at the top, **or** set an environment variable:

```bash
export YT_CHANNEL_ID="UCkBExJoIu47kqk8GXNj4ZYw"
```

---

## Running

### Start monitoring (real-time, runs forever)
```bash
python monitor.py
```

On first run it marks existing videos as "seen" so your CSV won't be flooded with old content.
From that point, every new upload gets automatically extracted within 5 minutes.

### Export existing videos (backfill)
```bash
python monitor.py --backfill
```
Exports the latest ~15 videos already on the channel (YouTube RSS only keeps ~15 entries).

### Change poll interval
Default is every 5 minutes. To change to 10 minutes:
```bash
export POLL_INTERVAL=600
python monitor.py
```

---

## Run in the background (Linux/Mac)

### Option A — nohup (simple)
```bash
nohup python monitor.py > /dev/null 2>&1 &
echo $! > monitor.pid
```
Stop it: `kill $(cat monitor.pid)`

### Option B — systemd service (recommended for servers)

Create `/etc/systemd/system/yt-monitor.service`:
```ini
[Unit]
Description=BJP4Karnataka YouTube Caption Monitor
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/path/to/youtube_monitor
Environment="YT_CHANNEL_ID=UCkBExJoIu47kqk8GXNj4ZYw"
ExecStart=/usr/bin/python3 /path/to/youtube_monitor/monitor.py
Restart=on-failure
RestartSec=30

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable yt-monitor
sudo systemctl start yt-monitor
sudo systemctl status yt-monitor
```

### Option C — Windows Task Scheduler
Set a scheduled task to run `python monitor.py` on system startup.

---

## Output files

| File | Purpose |
|---|---|
| `bjp4karnataka_captions.csv` | Your main data file — open in Excel/Sheets |
| `seen_videos.json` | Tracks processed video IDs (don't delete this) |
| `monitor.log` | Full activity log with timestamps |

---

## Notes

- **No API key needed** — uses YouTube's public RSS feed + open-source transcript library
- **Caption availability** — Captions must be enabled on the video (auto-generated or manual). If a video has no captions, `lang_used` will be `none` and `caption` will be empty.
- **Language preference** — tries Kannada (`kn`) first, then Hindi (`hi`), then English (`en`)
- **Shorts detection** — automatically labels Shorts vs regular Videos
- **RSS limit** — YouTube RSS only exposes the latest ~15 videos. For older videos, use `yt-dlp` separately.
