
cd ~/Downloads

cat > ps2_games_covers.sh <<'EOF'
#!/bin/bash
set -e

cd "$(dirname "$0")"

INPUT="$HOME/Downloads/ps2_games.json"
TREE="ps2_games_github_tree.json"
ZIP="ps2_covers_fallback.zip"
TEMP="ps2_covers_fallback"

if [ ! -f "$INPUT" ]; then
    echo "ERROR: ps2_games.json not found!"
    exit 1
fi

echo "Checking input JSON..."
jq -e 'type == "object"' "$INPUT" > /dev/null

echo "Downloading GitHub tree..."

URL="https://api.github.com/repos/igiteam/ps2-covers/git/trees/main?recursive=1"

SUCCESS=0

for ATTEMPT in 1 2 3 4; do
    echo "Attempt $ATTEMPT of 4..."

    if curl -fLsS \
        --retry 2 \
        --retry-delay 3 \
        --connect-timeout 20 \
        --max-time 180 \
        -H "Accept: application/vnd.github+json" \
        -H "User-Agent: PS2-Cover-Generator" \
        "$URL" -o "$TREE" \
        && jq -e '.tree | type == "array"' "$TREE" > /dev/null; then

        SUCCESS=1
        break
    fi

    sleep 3
done

if [ "$SUCCESS" -ne 1 ]; then
    echo "GitHub API unavailable. Trying ZIP fallback..."

    rm -rf "$TEMP"
    mkdir -p "$TEMP"

    if ! curl -fLsS \
        --retry 3 \
        --retry-delay 3 \
        --connect-timeout 20 \
        --max-time 300 \
        "https://codeload.github.com/igiteam/ps2-covers/zip/refs/heads/main" \
        -o "$ZIP"; then
        echo "ERROR: GitHub API and ZIP download both failed!"
        exit 1
    fi

    unzip -oq "$ZIP" -d "$TEMP"

    ROOT="$(find "$TEMP" -mindepth 1 -maxdepth 1 -type d | head -n 1)"

    if [ -z "$ROOT" ]; then
        echo "ERROR: ZIP extraction failed!"
        exit 1
    fi

    jq -n --arg root "$ROOT" '
      [
        ($root + "/covers"),
        ($root + "/covers/3d")
      ] as $dirs |
      [
        $dirs[] as $dir |
        if ($dir | endswith("/3d")) then
          (try (input_filename) catch empty)
        else empty end
      ]
    ' > /dev/null

    find "$ROOT/covers" -type f \
        \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" -o -iname "*.webp" \) \
        | sed "s|$ROOT/||" \
        | jq -R -s '
            split("\n") | map(select(length > 0)) |
            map({
              path: .,
              filename: (split("/") | last),
              name: (split("/") | last | sub("\\.[^.]+$"; ""))
            }) |
            {tree: map(. + {type: "blob"}), truncated: false}
          ' > "$TREE"
fi

echo "Matching games and covers..."

jq -n \
  --slurpfile games "$INPUT" \
  --slurpfile github "$TREE" '

  def normalize:
    gsub("//"; " ")
    | ascii_downcase
    | gsub("[^a-z0-9]"; "");

  def filename:
    split("/") | last;

  def find_cover($covers; $id; $title):
    (
      [$covers[] | select((.name | normalize) == ($id | normalize))][0] //
      [$covers[] | select((.name | normalize) == ($title | normalize))][0] //
      null
    );

  ($github[0].tree // []) as $tree |

  [
    $tree[]
    | select(.type == "blob")
    | select(.path | test("\\.(jpg|jpeg|png|webp)$"; "i"))
    | {
        path: .path,
        filename: (.path | filename),
        name: (.path | filename | sub("\\.[^.]+$"; ""))
      }
  ] as $all_covers |

  [
    $all_covers[]
    | select(.path | startswith("covers/"))
    | select((.path | startswith("covers/3d/")) | not)
  ] as $covers_2d |

  [
    $all_covers[]
    | select(.path | startswith("covers/3d/"))
  ] as $covers_3d |

  (
    $games[0]
    | to_entries
    | map(
        . as $game |

        ($game.value.serial // $game.key) as $id |
        ($game.value.title // "") as $title |

        (find_cover($covers_2d; $id; $title)) as $cover |
        (find_cover($covers_3d; $id; $title)) as $cover3d |

        {
          key: $game.key,
          value: (
            $game.value + {
              cover_url: (
                if $cover then
                  "https://raw.githubusercontent.com/igiteam/ps2-covers/refs/heads/main/"
                  + ($cover.path | split("/") | map(@uri) | join("/"))
                else "" end
              ),
              "3d_cover_url": (
                if $cover3d then
                  "https://raw.githubusercontent.com/igiteam/ps2-covers/refs/heads/main/"
                  + ($cover3d.path | split("/") | map(@uri) | join("/"))
                else "" end
              ),
              filename: (
                if $cover then $cover.filename else "" end
              )
            }
          )
        }
      )
    | from_entries
  )
' > ps2_games_pcsx.json

echo ""
echo "================================"
echo "PS2 JSON GENERATION COMPLETE"
echo "================================"
echo "Games:     $(jq 'length' ps2_games_pcsx.json)"
echo "2D covers: $(jq '[.[] | select(.cover_url != "")] | length' ps2_games_pcsx.json)"
echo "3D covers: $(jq '[.[] | select(."3d_cover_url" != "")] | length' ps2_games_pcsx.json)"
echo "No covers: $(jq '[.[] | select(.cover_url == "")] | length' ps2_games_pcsx.json)"
echo ""
echo "Output: ps2_games_pcsx.json"
EOF

chmod +x ps2_games_covers.sh
./ps2_games_covers.sh
