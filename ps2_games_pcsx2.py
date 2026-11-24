
#!/usr/bin/env python3
"""
PS2 Games Grid Generator
Creates an Xemu-style grid website from ps2_games_pcsx2.json.

Features:
- Alphabetical game sorting
- Search results automatically move to the top
- Original order restored when search is cleared
- Clickable game cards
- Automatic fallback titles when covers fail
- Search result counter
- Keyboard shortcut (/)
"""

import json
import os
import html as html_lib

# Configuration
JSON_FILE = "ps2_games_pcsx2.json"
OUTPUT_HTML = "index.html"

PLACEHOLDER_IMAGE = (
    "https://raw.githubusercontent.com/igiteam/ps2-covers/"
    "refs/heads/main/ps2-cover-default.png"
)

RAW_BASE_URL = (
    "https://raw.githubusercontent.com/igiteam/ps2-covers/"
    "refs/heads/main/default"
)


def load_games_data():
    """Load games and remove duplicates by title."""

    if not os.path.exists(JSON_FILE):
        print(f"❌ Error: {JSON_FILE} not found!")
        print("Please run the cover downloader first.")
        return None

    with open(JSON_FILE, "r", encoding="utf-8") as f:
        games = json.load(f)

    seen_titles = set()
    unique_games = []

    for game in games:
        title = game.get("title", "").strip()
        title_key = title.lower()

        if title_key not in seen_titles:
            seen_titles.add(title_key)
            unique_games.append(game)

    if len(unique_games) < len(games):
        print(
            f"✅ Removed {len(games) - len(unique_games)} "
            "duplicates by title"
        )

    print(f"✅ Loaded {len(unique_games)} unique games")
    return unique_games


def generate_html(games):
    """Generate the PS2 games grid website."""

    games.sort(key=lambda x: x.get("title", "").lower())

    total_games = len(games)

    with_2d = sum(
        1 for g in games
        if g.get("cover_url") != PLACEHOLDER_IMAGE
    )

    html = f"""<!DOCTYPE html>
<html lang="en">

<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">

  <title>PS2 Games Collection</title>

  <link rel="icon" href="https://raw.githubusercontent.com/igiteam/ps2-covers/refs/heads/main/ps2-icon.png" type="image/png">
  <link rel="apple-touch-icon" href="https://raw.githubusercontent.com/igiteam/ps2-covers/refs/heads/main/ps2-icon.png" sizes="180x180">

  <meta itemprop="name" content="PS2 Games Collection">
  <meta property="og:title" content="PS2 Games Collection">
  <meta property="og:type" content="website">
  <meta name="twitter:title" content="PS2 Games Collection">
  <meta name="twitter:card" content="summary_large_image">

  <style>
    body {{
      background-color: #1a1a1a;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI',
        Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
      margin: 4px 20px;
      padding: 0;
    }}

    #results {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
      gap: 10px;
      max-width: 1400px;
      margin: 4px auto 0;
      background-color: #1a1a1a;
      z-index: 1000;
    }}

    .title-card-link {{
      display: block;
      text-decoration: none;
      color: inherit;
      min-width: 0;
    }}

    .title-card {{
      background: #2a2a2a;
      border-radius: 8px;
      overflow: hidden;
      transition: transform 0.2s, opacity 0.2s;
    }}

    .title-card:hover {{
      transform: scale(1.05);
      z-index: 10;
    }}

    .title-card-container {{
      width: 100%;
      position: relative;
    }}

    .title-card-image-container {{
      width: 100%;
      aspect-ratio: 3/4;
      overflow: hidden;
      position: relative;
      background-color: #1a1a1a;
    }}

    .title-card-image-container img {{
      width: 100%;
      height: 100%;
      object-fit: cover;
      transition: opacity 0.3s;
    }}

    .title-card-image-container img.error {{
      opacity: 0;
    }}

    .title-card-image-container .fallback-title {{
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
      text-align: center;
      padding: 10px;
      box-sizing: border-box;
      background: linear-gradient(135deg, #2a2a2a 0%, #1a1a1a 100%);
      color: #888;
      font-size: 14px;
      font-weight: 500;
      word-break: break-word;
      border: 1px solid #333;
    }}

    .fill-color-Playable {{
      background-color: #42991b !important;
      color: white !important;
      font-weight: 700 !important;
    }}

    .card-body {{
      flex: 1 1 auto;
      min-height: 1px;
      padding: 0.5rem 1.25rem !important;
    }}

    .text-center {{
      text-align: center !important;
    }}

    .py-1 {{
      padding-top: 0.25rem !important;
      padding-bottom: 0.25rem !important;
    }}

    .my-0 {{
      margin-top: 0 !important;
      margin-bottom: 0 !important;
    }}

    small {{
      font-size: 80%;
    }}

    a {{
      text-decoration: none;
      color: inherit;
    }}

    #saved-search-container {{
      position: sticky;
      top: 0;
      z-index: 10000;
      margin: 8px 0;
      background-color: #1a1a1a;
    }}

    #saved-search-input {{
      padding: 10px;
      width: calc(100% - 20px);
      border: 1px solid #555;
      border-radius: 4px;
      background: #444;
      color: white;
      flex: 1;
      min-width: 0;
    }}

    .search-row {{
      display: flex;
      align-items: center;
      gap: 10px;
    }}

    .icon {{
      width: 34px;
      height: 34px;
      border-radius: 4px;
      object-fit: cover;
      flex-shrink: 0;
    }}

    #saved-search-input::placeholder {{
      color: #aaa;
    }}

    #saved-results-count {{
      color: white;
      font-size: 14px;
      text-align: center;
      margin-top: 5px;
    }}

    .hidden-game {{
      display: none !important;
    }}
  </style>
</head>

<body>

  <div id="saved-search-container">
    <div class="search-row">

      <img
        src="https://raw.githubusercontent.com/igiteam/ps2-covers/refs/heads/main/ps2-icon.png"
        class="icon"
        alt="PS2 logo"
      >

      <input
        type="text"
        id="saved-search-input"
        placeholder="Search games..."
        autocomplete="off"
      >

      <a
        href="https://www.ebay.co.uk/sch/i.html?_nkw=2x+ps2+controller+with+usb+adapter"
        target="_blank"
        rel="noopener noreferrer"
      >
        <img
          src="https://raw.githubusercontent.com/igiteam/ps2-covers/refs/heads/main/ps2-controller.png"
          class="icon"
          alt="PS2 Controller"
        >
      </a>

      <a
        href="https://igiteam.github.io/ps2magazines/"
        target="_blank"
        rel="noopener noreferrer"
      >
        <img
          src="https://raw.githubusercontent.com/igiteam/ps2-covers/refs/heads/main/ps2-magazine.png"
          class="icon"
          alt="PS2 Magazine"
        >
      </a>

    </div>

    <div id="saved-results-count"></div>
  </div>

  <div class="row" id="results">
"""

    # Generate game cards
    for game in games:

        title = game.get("title", "").strip()

        # Safely escape HTML characters
        safe_title = html_lib.escape(title, quote=True)

        cover_url = game.get("cover_url", PLACEHOLDER_IMAGE)
        cover_3d_url = game.get("cover_3d_url", PLACEHOLDER_IMAGE)

        if cover_url and cover_url != PLACEHOLDER_IMAGE:
            selected_cover = cover_url
            has_real_cover = True

        elif cover_3d_url and cover_3d_url != PLACEHOLDER_IMAGE:
            selected_cover = cover_3d_url
            has_real_cover = True

        else:
            selected_cover = PLACEHOLDER_IMAGE
            has_real_cover = False

        safe_cover = html_lib.escape(selected_cover, quote=True)

        title_display = "flex" if not has_real_cover else "none"

        html += f"""
    <div
      class="col px-1 mb-4 title-card"
      data-title-name="{safe_title}"
      data-title-status="Play"
    >

      <a
        target="_blank"
        rel="noopener noreferrer"
        href="https://github.com/igiteam/ps2-covers"
      >

        <div class="mx-auto title-card-container">

          <div
            class="title-card-image-container"
            style="position: relative;"
          >

            <img
              src="{safe_cover}"
              loading="lazy"
              title="{safe_title}"
              alt="{safe_title}"
              onerror="
                this.classList.add('error');
                this.src='{PLACEHOLDER_IMAGE}';
                this.parentNode.querySelector('.fallback-title').style.display='flex';
              "
            >

            <div
              class="fallback-title"
              style="
                display: {title_display};
                position: absolute;
                bottom: 0;
                left: 0;
                right: 0;
                background: linear-gradient(transparent, rgba(0,0,0,0.9));
                color: white;
                padding: 15px 8px 8px 8px;
                font-size: 12px;
                text-align: center;
                font-weight: 500;
              "
            >{safe_title}</div>

          </div>

          <div class="fill-color-Playable card-body text-center py-1 my-0">
            <small><strong>Play</strong></small>
          </div>

        </div>

      </a>

    </div>
"""

    html += """
  </div>

  <script>
  document.addEventListener('DOMContentLoaded', function () {

    const resultsContainer = document.getElementById('results');
    const searchInput = document.getElementById('saved-search-input');
    const resultsCount = document.getElementById('saved-results-count');

    // ==========================================
    // WRAP GAME CARDS WITH SEARCH LINKS
    // ==========================================

    function wrapCardsWithLinks() {

      document.querySelectorAll('.title-card').forEach(card => {

        // Do not wrap a card more than once
        if (card.parentElement?.classList.contains('title-card-link')) {
          return;
        }

        const title = card.getAttribute('data-title-name');
        const serial = card.getAttribute('data-serial');
        const status = card.getAttribute('data-title-status');

        // Remove the original inner GitHub link
        const existingInnerLink = card.querySelector('a');

        if (existingInnerLink) {
          while (existingInnerLink.firstChild) {
            card.insertBefore(existingInnerLink.firstChild, existingInnerLink);
          }

          existingInnerLink.remove();
        }

        // Create URL slug
        let urlPath = '';

        if (title) {
          urlPath = title
            .toLowerCase()
            .replace(/[^\\w\\s-]/g, '')
            .replace(/\\s+/g, '-')
            .replace(/-+/g, '-')
            .replace(/^-|-$/g, '');

        } else if (serial) {
          urlPath = serial;
        }

        if (!urlPath) return;

        const urlParams = new URLSearchParams(window.location.search);
        const targetUrl = urlParams.get('url');

        const link = document.createElement('a');

        if (targetUrl) {
          link.href = targetUrl.replace(/\\/$/, '') + '/PS2/' + urlPath;
        } else {
          link.href =
            'https://meyt.macosxjs.com/search/' +
            encodeURIComponent(urlPath + ' PS2');
        }

        link.className = 'title-card-link';
        link.rel = 'noopener noreferrer';
        link.target = '_blank';

        link.style.display = 'block';
        link.style.textDecoration = 'none';
        link.style.color = 'inherit';

        // Copy data attributes
        if (title) {
          link.setAttribute('data-title-name', title);
        }

        if (serial) {
          link.setAttribute('data-serial', serial);
        }

        if (status) {
          link.setAttribute('data-title-status', status);
        }

        // Wrap the card
        card.parentNode.insertBefore(link, card);
        link.appendChild(card);

      });
    }

    wrapCardsWithLinks();

    // ==========================================
    // SAVE ORIGINAL ALPHABETICAL ORDER
    // ==========================================

    const originalLinks = Array.from(
      resultsContainer.querySelectorAll(':scope > .title-card-link')
    );

    // ==========================================
    // SEARCH AND REORDER
    // ==========================================

    searchInput.addEventListener('input', function (e) {

      const searchTerm = e.target.value.toLowerCase().trim();

      const matchingLinks = [];
      const remainingLinks = [];

      originalLinks.forEach(link => {

        const title = (
          link.getAttribute('data-title-name') || ''
        ).toLowerCase();

        if (searchTerm && title.includes(searchTerm)) {
          matchingLinks.push(link);
        } else {
          remainingLinks.push(link);
        }

      });

      // Matching cards first, remaining cards afterwards
      const orderedLinks = searchTerm
        ? [...matchingLinks, ...remainingLinks]
        : originalLinks;

      orderedLinks.forEach(link => {

        const isMatch = matchingLinks.includes(link);

        // Hide non-matching cards
        link.classList.toggle(
          'hidden-game',
          !!searchTerm && !isMatch
        );

        // Physically reorder cards inside the grid
        resultsContainer.appendChild(link);

      });

      // Update results counter
      resultsCount.textContent = searchTerm
        ? `Found ${matchingLinks.length} game${matchingLinks.length !== 1 ? 's' : ''}`
        : '';

    });

    // ==========================================
    // KEYBOARD SHORTCUT
    // ==========================================

    document.addEventListener('keydown', function (e) {

      if (
        e.key === '/' &&
        !e.ctrlKey &&
        !e.metaKey &&
        !e.altKey &&
        document.activeElement !== searchInput
      ) {
        e.preventDefault();
        searchInput.focus();
      }

      // Escape clears search
      if (e.key === 'Escape' && document.activeElement === searchInput) {
        searchInput.value = '';
        searchInput.dispatchEvent(new Event('input'));
        searchInput.blur();
      }

    });

  });
  </script>

</body>
</html>
"""

    return html


def main():

    print("🎮 PS2 Games Grid Generator (Xemu Style)")
    print("=" * 50)

    games = load_games_data()

    if not games:
        return

    print("🔄 Generating grid website...")

    html_content = generate_html(games)

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"✅ Website generated: {OUTPUT_HTML}")

    print("\\n📊 Statistics:")
    print(f"   - Total games: {len(games)}")
    print(f"   - With 2D covers: {sum(1 for g in games if g.get('cover_url') != PLACEHOLDER_IMAGE)}")


if __name__ == "__main__":
    main()
