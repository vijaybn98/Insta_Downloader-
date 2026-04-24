import os
import re
import zipfile
import shutil
import tempfile
import traceback
from pathlib import Path

from flask import Flask, request, jsonify, send_file, make_response
import instaloader

app = Flask(__name__)

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

L = instaloader.Instaloader(
    download_pictures=True,
    download_videos=True,
    download_video_thumbnails=False,
    download_geotags=False,
    download_comments=False,
    save_metadata=False,
    compress_json=False,
    quiet=True,
)

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>InstaGrab — Instagram Downloader</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:wght@300;400;500&display=swap" rel="stylesheet" />
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
      --bg:       #0a090f;
      --surface:  #12101a;
      --border:   #261f3a;
      --text:     #ede8ff;
      --muted:    #6b5f8a;
      --g1:       #e1306c;
      --g2:       #833ab4;
      --g3:       #fd1d1d;
      --g4:       #fcb045;
      --accent:   #c13584;
      --success:  #2dce89;
      --error:    #f5365c;
      --radius:   14px;
    }

    html { scroll-behavior: smooth; }

    body {
      background-color: #0a090f;
      color: #ede8ff;
      font-family: 'DM Mono', monospace;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 48px 20px 80px;
      position: relative;
      overflow-x: hidden;
    }

    /* Ambient background blobs */
    body::before, body::after {
      content: '';
      position: fixed;
      border-radius: 50%;
      filter: blur(120px);
      opacity: 0.18;
      pointer-events: none;
      z-index: 0;
    }
    body::before {
      width: 600px; height: 600px;
      background: radial-gradient(circle, #833ab4, transparent 70%);
      top: -200px; left: -200px;
    }
    body::after {
      width: 500px; height: 500px;
      background: radial-gradient(circle, #e1306c, transparent 70%);
      bottom: -150px; right: -150px;
    }

    .wrapper {
      width: 100%;
      max-width: 640px;
      position: relative;
      z-index: 1;
    }

    /* ── Header ── */
    header {
      text-align: center;
      margin-bottom: 48px;
      animation: fadeDown 0.6s ease both;
    }

    .logo-icon {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 64px; height: 64px;
      border-radius: 18px;
      background: linear-gradient(135deg, var(--g2), var(--g1), var(--g4));
      margin-bottom: 20px;
      box-shadow: 0 0 40px rgba(225, 48, 108, 0.35);
    }
    .logo-icon svg { width: 34px; height: 34px; fill: #fff; }

    h1 {
      font-family: 'Syne', sans-serif;
      font-size: clamp(2rem, 5vw, 2.8rem);
      font-weight: 800;
      letter-spacing: -0.03em;
      background: linear-gradient(120deg, #fff 30%, #c680f5 70%, #e1306c 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      margin-bottom: 10px;
    }

    .tagline {
      color: var(--muted);
      font-size: 0.85rem;
      letter-spacing: 0.05em;
      text-transform: uppercase;
    }

    /* ── Card ── */
    .card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 20px;
      padding: 32px;
      margin-bottom: 16px;
      animation: fadeUp 0.5s ease both;
    }

    .card-title {
      font-family: 'Syne', sans-serif;
      font-size: 0.7rem;
      font-weight: 600;
      letter-spacing: 0.15em;
      text-transform: uppercase;
      color: var(--muted);
      margin-bottom: 16px;
    }

    /* ── Input ── */
    .input-wrap {
      position: relative;
      margin-bottom: 20px;
    }
    .input-wrap svg {
      position: absolute;
      left: 16px;
      top: 50%;
      transform: translateY(-50%);
      width: 18px; height: 18px;
      stroke: var(--muted);
      fill: none;
      stroke-width: 2;
      pointer-events: none;
      transition: stroke 0.2s;
    }
    .input-wrap:focus-within svg { stroke: var(--accent); }

    input[type="text"], input[type="password"] {
      width: 100%;
      background: rgba(255,255,255,0.04);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      color: var(--text);
      font-family: 'DM Mono', monospace;
      font-size: 0.9rem;
      padding: 14px 16px 14px 46px;
      outline: none;
      transition: border-color 0.2s, box-shadow 0.2s, background 0.2s;
    }
    input::placeholder { color: var(--muted); }
    input:focus {
      border-color: var(--accent);
      background: rgba(193, 53, 132, 0.06);
      box-shadow: 0 0 0 3px rgba(193, 53, 132, 0.12);
    }

    /* ── Type Selector ── */
    .type-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 10px;
      margin-bottom: 24px;
    }

    .type-btn {
      display: flex;
      align-items: center;
      gap: 10px;
      background: rgba(255,255,255,0.03);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 14px 16px;
      cursor: pointer;
      transition: all 0.2s;
      color: var(--muted);
      font-family: 'DM Mono', monospace;
      font-size: 0.82rem;
      text-align: left;
    }
    .type-btn svg { width: 18px; height: 18px; flex-shrink: 0; }
    .type-btn span { font-size: 0.78rem; }
    .type-btn:hover { border-color: var(--accent); color: var(--text); }
    .type-btn.active {
      border-color: var(--accent);
      background: rgba(193, 53, 132, 0.12);
      color: var(--text);
      box-shadow: 0 0 0 1px var(--accent);
    }

    /* ── Download Button ── */
    .btn-download {
      width: 100%;
      background: linear-gradient(135deg, #833ab4, #c13584, #e1306c);
      border: none;
      border-radius: var(--radius);
      color: #fff;
      font-family: 'Syne', sans-serif;
      font-size: 1rem;
      font-weight: 700;
      letter-spacing: 0.04em;
      padding: 16px;
      cursor: pointer;
      transition: opacity 0.2s, transform 0.15s, box-shadow 0.2s;
      box-shadow: 0 4px 24px rgba(193, 53, 132, 0.4);
      position: relative;
      overflow: hidden;
    }
    .btn-download::after {
      content: '';
      position: absolute;
      inset: 0;
      background: linear-gradient(135deg, transparent 40%, rgba(255,255,255,0.12));
    }
    .btn-download:hover:not(:disabled) { opacity: 0.92; transform: translateY(-1px); box-shadow: 0 8px 30px rgba(193, 53, 132, 0.5); }
    .btn-download:active:not(:disabled) { transform: translateY(0); }
    .btn-download:disabled { opacity: 0.45; cursor: not-allowed; }

    /* ── Credentials (collapsed) ── */
    .creds-toggle {
      display: flex;
      align-items: center;
      gap: 8px;
      background: none;
      border: none;
      color: var(--muted);
      font-family: 'DM Mono', monospace;
      font-size: 0.78rem;
      cursor: pointer;
      padding: 4px 0;
      margin-top: 14px;
      transition: color 0.2s;
    }
    .creds-toggle:hover { color: var(--text); }
    .creds-toggle svg { width: 14px; height: 14px; transition: transform 0.3s; }
    .creds-toggle.open svg { transform: rotate(180deg); }

    .creds-panel {
      display: none;
      margin-top: 14px;
      padding: 18px;
      background: rgba(255,255,255,0.025);
      border: 1px dashed var(--border);
      border-radius: var(--radius);
      gap: 12px;
      flex-direction: column;
    }
    .creds-panel.open { display: flex; }

    .creds-note {
      font-size: 0.72rem;
      color: var(--muted);
      line-height: 1.6;
    }
    .creds-note strong { color: #fcb045; }

    /* ── Status ── */
    #status {
      margin-top: 20px;
      display: none;
      animation: fadeUp 0.3s ease both;
    }

    .status-inner {
      display: flex;
      align-items: flex-start;
      gap: 14px;
      padding: 18px 20px;
      border-radius: var(--radius);
      border: 1px solid transparent;
    }

    .status-inner.loading {
      background: rgba(255,255,255,0.04);
      border-color: var(--border);
      color: var(--muted);
    }
    .status-inner.success {
      background: rgba(45, 206, 137, 0.08);
      border-color: rgba(45, 206, 137, 0.3);
      color: var(--success);
    }
    .status-inner.error {
      background: rgba(245, 54, 92, 0.08);
      border-color: rgba(245, 54, 92, 0.3);
      color: var(--error);
    }

    .status-icon { flex-shrink: 0; width: 20px; height: 20px; margin-top: 1px; }
    .status-text { font-size: 0.85rem; line-height: 1.6; }
    .status-text strong { display: block; font-family: 'Syne', sans-serif; font-size: 0.9rem; margin-bottom: 2px; }

    /* Spinner */
    @keyframes spin { to { transform: rotate(360deg); } }
    .spinner {
      width: 20px; height: 20px; border-radius: 50%;
      border: 2px solid var(--border);
      border-top-color: var(--accent);
      animation: spin 0.7s linear infinite;
      flex-shrink: 0;
    }

    /* ── Tips ── */
    .tips {
      margin-top: 12px;
      animation: fadeUp 0.7s 0.1s ease both;
    }
    .tips-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 8px;
    }
    .tip {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 12px 14px;
      font-size: 0.73rem;
      color: var(--muted);
      line-height: 1.5;
    }
    .tip .tip-label {
      color: var(--text);
      font-family: 'Syne', sans-serif;
      font-size: 0.72rem;
      font-weight: 600;
      margin-bottom: 3px;
      display: flex;
      align-items: center;
      gap: 5px;
    }

    /* ── Footer ── */
    footer {
      margin-top: 48px;
      text-align: center;
      color: var(--muted);
      font-size: 0.72rem;
      line-height: 1.8;
      animation: fadeUp 0.8s 0.2s ease both;
    }

    /* ── Animations ── */
    @keyframes fadeDown {
      from { opacity: 0; transform: translateY(-20px); }
      to   { opacity: 1; transform: translateY(0); }
    }
    @keyframes fadeUp {
      from { opacity: 0; transform: translateY(16px); }
      to   { opacity: 1; transform: translateY(0); }
    }

    @media (max-width: 480px) {
      .type-grid { grid-template-columns: repeat(2, 1fr); }
      .tips-grid { grid-template-columns: 1fr; }
      .card { padding: 22px; }
    }
  </style>
</head>
<body>
<div class="wrapper">

  <!-- Header -->
  <header>
    <div class="logo-icon">
      <svg viewBox="0 0 24 24"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/></svg>
    </div>
    <h1>InstaGrab</h1>
    <p class="tagline">Download posts · reels · stories · profile pics</p>
  </header>

  <!-- Main Card -->
  <div class="card">
    <div class="input-wrap">
      <svg viewBox="0 0 24 24"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>
      <input type="text" id="urlInput" placeholder="Paste any Instagram URL — post, reel, story or profile" />
    </div>

    <button class="btn-download" id="dlBtn" onclick="startDownload()">
      ↓ &nbsp;Download
    </button>

    <!-- Optional credentials -->
    <button class="creds-toggle" id="credsToggle" onclick="toggleCreds()">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
      Login (required for Stories &amp; private accounts)
    </button>

    <div class="creds-panel" id="credsPanel">
      <p class="creds-note"><strong>⚠ Optional:</strong> Credentials are sent only to your local server and never stored. Required for Stories &amp; private profiles.</p>
      <div class="input-wrap" style="margin:0">
        <svg viewBox="0 0 24 24"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
        <input type="text" id="igUser" placeholder="Instagram username" autocomplete="off" />
      </div>
      <div class="input-wrap" style="margin:0">
        <svg viewBox="0 0 24 24"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
        <input type="password" id="igPass" placeholder="Password" autocomplete="off" />
      </div>
    </div>
  </div>

  <!-- Status -->
  <div id="status">
    <div class="status-inner" id="statusInner">
      <div class="status-icon" id="statusIcon"></div>
      <div class="status-text" id="statusText"></div>
    </div>
  </div>

  <!-- Tips -->
  <div class="tips">
    <div class="tips-grid">
      <div class="tip">
        <div class="tip-label">📄 Posts</div>
        Paste the full post URL. Multi-image posts are bundled as a .zip.
      </div>
      <div class="tip">
        <div class="tip-label">🎬 Reels</div>
        Works with /reel/ and /p/ URLs. Downloads the highest quality MP4.
      </div>
      <div class="tip">
        <div class="tip-label">📖 Stories</div>
        Requires login. Enter the account's username (not your own).
      </div>
      <div class="tip">
        <div class="tip-label">👤 Profile pic</div>
        Enter just a username or a profile URL to grab the full-res avatar.
      </div>
    </div>
  </div>

  <footer>
    Built with Flask + Instaloader · For personal use only<br>
    Respect creators' content and Instagram's Terms of Service
  </footer>

</div>

<script>
  function toggleCreds() {
    const panel = document.getElementById('credsPanel');
    const toggle = document.getElementById('credsToggle');
    panel.classList.toggle('open');
    toggle.classList.toggle('open');
  }

  function showStatus(state, title, message) {
    const box = document.getElementById('status');
    const inner = document.getElementById('statusInner');
    const icon = document.getElementById('statusIcon');
    const text = document.getElementById('statusText');

    box.style.display = 'block';
    inner.className = 'status-inner ' + state;

    if (state === 'loading') {
      icon.innerHTML = '<div class="spinner"></div>';
    } else if (state === 'success') {
      icon.innerHTML = `<svg class="status-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>`;
    } else {
      icon.innerHTML = `<svg class="status-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>`;
    }

    text.innerHTML = `<strong>${title}</strong>${message}`;
  }

  async function startDownload() {
    const url = document.getElementById('urlInput').value.trim();
    if (!url) {
      showStatus('error', 'URL required', 'Please paste an Instagram URL or enter a username.');
      return;
    }

    const btn = document.getElementById('dlBtn');
    btn.disabled = true;
    showStatus('loading', 'Fetching content…', 'Contacting Instagram — this may take a few seconds.');

    try {
      const payload = {
        url,
        ig_user: document.getElementById('igUser').value.trim(),
        ig_pass: document.getElementById('igPass').value.trim(),
      };

      const res = await fetch('/api/download', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const err = await res.json();
        showStatus('error', 'Download failed', err.error || 'Unknown error. Check the URL and try again.');
        return;
      }

      // Trigger browser download
      const blob = await res.blob();
      const cd = res.headers.get('Content-Disposition') || '';
      const nameMatch = cd.match(/filename="?([^"]+)"?/);
      const filename = nameMatch ? nameMatch[1] : 'instagram_download';

      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();

      showStatus('success', 'Download started!', `Saved as <strong>${filename}</strong>. Check your downloads folder.`);
    } catch (e) {
      showStatus('error', 'Network error', 'Could not reach the server. Make sure Flask is running on port 5000.');
    } finally {
      btn.disabled = false;
    }
  }

  // Allow Enter key
  document.getElementById('urlInput').addEventListener('keydown', e => {
    if (e.key === 'Enter') startDownload();
  });
</script>
</body>
</html>
"""


def detect_url_type(url: str):
    """Return ('post', shortcode) | ('story', username) | ('profile', username) | (None, None)"""
    url = url.strip()
    # Post / Reel / IGTV
    m = re.search(r"instagram\.com/(?:p|reel|tv)/([A-Za-z0-9_-]+)", url)
    if m:
        return "post", m.group(1)
    # Stories URL: instagram.com/stories/<username>/...
    m = re.search(r"instagram\.com/stories/([A-Za-z0-9._]+)", url)
    if m:
        return "story", m.group(1)
    # Profile URL or plain username
    url_clean = url.rstrip("/")
    m = re.search(r"instagram\.com/([A-Za-z0-9._]+)/?$", url_clean)
    if m:
        return "profile", m.group(1)
    # Plain username (no URL at all)
    if re.match(r"^[A-Za-z0-9._]+$", url_clean):
        return "profile", url_clean
    return None, None


def clean_dir(path: Path):
    if path.exists():
        shutil.rmtree(path)


def zip_and_send(media_files, zip_name):
    zip_path = media_files[0].parent / zip_name
    with zipfile.ZipFile(zip_path, "w") as zf:
        for f in media_files:
            zf.write(f, f.name)
    return send_file(zip_path, as_attachment=True, download_name=zip_name)


@app.route("/")
def index():
    return make_response(HTML_PAGE, 200, {"Content-Type": "text/html; charset=utf-8"})


@app.route("/api/download", methods=["POST"])
def download_content():
    data = request.get_json(force=True)
    url = (data.get("url") or "").strip()
    ig_user = (data.get("ig_user") or "").strip()
    ig_pass = (data.get("ig_pass") or "").strip()

    if not url:
        return jsonify({"error": "Please paste an Instagram URL or username."}), 400

    # Optional login (needed for private accounts & stories)
    if ig_user and ig_pass:
        try:
            L.login(ig_user, ig_pass)
        except Exception as e:
            return jsonify({"error": f"Login failed: {e}"}), 401

    kind, value = detect_url_type(url)
    if not kind:
        return jsonify({"error": "Unrecognised URL. Paste a post, reel, story or profile link."}), 400

    tmp = Path(tempfile.mkdtemp(dir=DOWNLOAD_DIR))
    try:
        # ── Post / Reel / IGTV ───────────────────────────────────────────────
        if kind == "post":
            post = instaloader.Post.from_shortcode(L.context, value)
            L.download_post(post, target=tmp)
            media = [f for f in tmp.glob("*")
                     if f.suffix.lower() in (".jpg", ".jpeg", ".png", ".mp4", ".webp")]
            if not media:
                return jsonify({"error": "No media found for this post."}), 404
            if len(media) == 1:
                return send_file(media[0], as_attachment=True, download_name=media[0].name)
            return zip_and_send(media, "instagram_post.zip")

        # ── Stories ──────────────────────────────────────────────────────────
        if kind == "story":
            if not ig_user:
                return jsonify({"error": "Stories require Instagram login. Fill in the credentials below."}), 403
            profile = instaloader.Profile.from_username(L.context, value)
            L.download_stories(userids=[profile.userid], filename_target=str(tmp))
            media = list(tmp.rglob("*.mp4")) + list(tmp.rglob("*.jpg")) + list(tmp.rglob("*.png"))
            if not media:
                return jsonify({"error": "No active stories found (they may have expired)."}), 404
            return zip_and_send(media, f"{value}_stories.zip")

        # ── Profile picture ──────────────────────────────────────────────────
        if kind == "profile":
            profile = instaloader.Profile.from_username(L.context, value)
            L.download_profilepic(profile)
            profile_dir = Path(value)
            pics = list(profile_dir.glob("*.jpg")) + list(profile_dir.glob("*.png"))
            if not pics:
                return jsonify({"error": "Could not retrieve profile picture."}), 404
            latest = max(pics, key=lambda f: f.stat().st_mtime)
            out = tmp / latest.name
            shutil.copy(latest, out)
            clean_dir(profile_dir)
            return send_file(out, as_attachment=True, download_name=latest.name)

    except instaloader.exceptions.LoginRequiredException:
        return jsonify({"error": "This account is private. Provide your Instagram credentials below."}), 403
    except instaloader.exceptions.ProfileNotExistsException:
        return jsonify({"error": "Profile not found — double-check the username."}), 404
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
