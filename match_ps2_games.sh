cd ~/Downloads

cat > ps2_match_covers.sh <<'EOF'
#!/bin/bash
set -e

INPUT="$HOME/Downloads/ps2_games_titles_unique.json"
TREE="$HOME/Downloads/ps2_games_github_tree.json"
OUTPUT="$HOME/Downloads/ps2_games_pcsx.json"

BASE="https://raw.githubusercontent.com/igiteam/ps2-covers/refs/heads/main"
PLACEHOLDER="$BASE/ps2-cover-default.png"

if [ ! -f "$INPUT" ] || [ ! -f "$TREE" ]; then
    echo "ERROR: Input or GitHub tree file is missing."
    exit 1
fi

echo "Building cover index..."
echo "Matching game IDs..."

jq -n \
  --slurpfile games "$INPUT" \
  --slurpfile tree "$TREE" \
  --arg base "$BASE" \
  --arg placeholder "$PLACEHOLDER" '

  (
    reduce ($tree[0].tree[]?) as $file
      ({};
        ($file.path // "") as $path
        | if ($path | startswith("covers/default/")) then
            ($path | split("/")[-1] | split(".")[0] | ascii_upcase) as $id
            | .[$id] = (.[$id] // {}) + {
                "2d": ($base + "/" + $path)
              }
          elif ($path | startswith("covers/3d/")) then
            ($path | split("/")[-1] | split(".")[0] | ascii_upcase) as $id
            | .[$id] = (.[$id] // {}) + {
                "3d": ($base + "/" + $path)
              }
          else .
          end
      )
  ) as $index

  | [
      $games[0][]
      | . as $game
      | ($game.id | ascii_upcase) as $id
      | ($index[$id] // {}) as $cover
      | {
          id: $game.id,
          title: $game.title,
          cover_url: ($cover["2d"] // $placeholder),
          cover_3d_url: ($cover["3d"] // $placeholder)
        }
    ]
' > "$OUTPUT"

TOTAL=$(jq 'length' "$OUTPUT")
COVER_2D=$(jq --arg p "$PLACEHOLDER" '[.[] | select(.cover_url != $p)] | length' "$OUTPUT")
COVER_3D=$(jq --arg p "$PLACEHOLDER" '[.[] | select(.cover_3d_url != $p)] | length' "$OUTPUT")
MISSING_2D=$(jq --arg p "$PLACEHOLDER" '[.[] | select(.cover_url == $p)] | length' "$OUTPUT")
MISSING_3D=$(jq --arg p "$PLACEHOLDER" '[.[] | select(.cover_3d_url == $p)] | length' "$OUTPUT")
BOTH_MISSING=$(jq --arg p "$PLACEHOLDER" '[.[] | select(.cover_url == $p and .cover_3d_url == $p)] | length' "$OUTPUT")

echo ""
echo "======================================"
echo "PS2 COVER MATCHING COMPLETE"
echo "======================================"
echo ""
echo "TOTAL ENTRIES: $TOTAL"
echo ""
echo "2D covers found: $COVER_2D"
echo "2D placeholders: $MISSING_2D"
echo ""
echo "3D covers found: $COVER_3D"
echo "3D placeholders: $MISSING_3D"
echo ""
echo "Missing both covers: $BOTH_MISSING"
echo ""
echo "Output: $OUTPUT"
echo ""
echo "======================================"
echo "FIRST 3 ENTRIES"
echo "======================================"
jq '.[0:3]' "$OUTPUT"
echo ""
echo "======================================"
echo "FINAL ENTRY COUNT: $TOTAL"
echo "======================================"
EOF

chmod +x ps2_match_covers.sh
./ps2_match_covers.sh
