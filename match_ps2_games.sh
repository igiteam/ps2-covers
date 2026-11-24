(
set -e

INPUT="$HOME/Downloads/ps2_games.json"

if [ ! -f "$INPUT" ]; then
    echo "ERROR: ps2_games.json not found!"
    exit 1
fi

echo "Downloading GitHub tree..."

curl -fsSL \
"https://api.github.com/repos/igiteam/ps2-covers/git/trees/main?recursive=1" \
-o ps2_games_github_tree.json

echo "Matching games and covers..."

jq -n \
  --slurpfile games "$INPUT" \
  --slurpfile github ps2_games_github_tree.json '

  def normalize:
    gsub("//"; " ")
    | ascii_downcase
    | gsub("[^a-z0-9]"; "");

  def filename:
    split("/") | last;

  def find_cover($covers; $id; $title):
    (
      [
        $covers[]
        | select((.name | normalize) == ($id | normalize))
      ][0] //
      [
        $covers[]
        | select((.name | normalize) == ($title | normalize))
      ][0] //
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

  [
    $games[0][] as $game |

    ($game["Game ID"] // "") as $id |
    ($game["Title"] // "") as $title |

    (find_cover($covers_2d; $id; $title)) as $cover |
    (find_cover($covers_3d; $id; $title)) as $cover3d |

    {
      title: $title,

      cover_url: (
        if $cover then
          "https://raw.githubusercontent.com/igiteam/ps2-covers/refs/heads/main/"
          + ($cover.path | split("/") | map(@uri) | join("/"))
        else ""
        end
      ),

      "3d_cover_url": (
        if $cover3d then
          "https://raw.githubusercontent.com/igiteam/ps2-covers/refs/heads/main/"
          + ($cover3d.path | split("/") | map(@uri) | join("/"))
        else ""
        end
      ),

      filename: (
        if $cover then $cover.filename else "" end
      )
    }
  ]
' > ps2_games_pcsx.json

echo ""
echo "================================"
echo "PS2 JSON GENERATION COMPLETE"
echo "================================"
echo "Games:     $(jq length ps2_games_pcsx.json)"
echo "2D covers: $(jq '[.[] | select(.cover_url != "")] | length' ps2_games_pcsx.json)"
echo "3D covers: $(jq '[.[] | select(."3d_cover_url" != "")] | length' ps2_games_pcsx.json)"
echo "No covers: $(jq '[.[] | select(.cover_url == "")] | length' ps2_games_pcsx.json)"
)
