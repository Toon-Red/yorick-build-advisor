# Yorick Build Advisor

A decision-tree build advisor for League of Legends Yorick, based on [Kampsycho's guide](https://docs.google.com/document/d/1AHaEfMCoSsyx3HpZmk2mEFnRiiwnB8CkGAYqzjhDJo/edit). No AI hallucination — all build logic is hardcoded from the source material.

## Features

- **71 matchups** with guide-accurate keystones, items, runes, and summoner spells
- **Live champ select detection** — auto-detects enemies via LCU (League Client API)
- **Auto-import** runes, items, and summoner spells directly into the League client
- **Desktop app** — native Windows window via WebView2, pinnable to taskbar
- **Auto-updater** — checks GitHub releases on startup, one-click update
- **Decision tree engine** — resolve adaptation (A/B/C), shard selection, starter items, item paths

## Download

Grab the latest installer from the [Releases](https://github.com/Toon-Red/yorick-build-advisor/releases/latest) page:

- **`YorickBuildAdvisor_Setup.exe`** — installer with Start Menu shortcut, taskbar pinning, and uninstaller
- **`YorickBuildAdvisor.exe`** — standalone portable exe (no install needed)

> Windows SmartScreen may show a warning since the app isn't code-signed. Click "More info" → "Run anyway".

## How It Works

```
User selects: [Yorick] vs [Enemy]
                    ↓
           Decision Tree Engine
                    ↓
    1. Matchup lookup       → difficulty, recommended keystones
    2. Resolve adaptation   → A/B/C (default/poke/burst)
    3. Shard selection      → MS/HP/Adaptive based on enemy
    4. Summoner spells      → Ghost+Ignite / Exhaust / etc.
    5. Starter items        → based on enemy type
    6. Item path            → based on matchup category
                    ↓
    Returns ranked list of full build options
    (rune page IDs + item IDs + reasoning text)
```

Each build option includes:
- Full 9 rune perk IDs (ready for LCU import)
- Full item set with IDs
- Difficulty rating, summoner spells, starter items
- Reasoning text from the guide (not AI-generated)

## Development

### Prerequisites

- Python 3.10+
- Windows (for WebView2 desktop app and LCU integration)

### Setup

```bash
git clone https://github.com/Toon-Red/yorick-build-advisor.git
cd yorick-build-advisor
pip install -r requirements.txt
```

### Run (dev server)

```bash
python app.py
# Opens at http://127.0.0.1:5001
```

### Run (desktop app)

```bash
pip install webview2 pywin32
python launcher.py
```

### Run tests

```bash
python -m pytest tests/ -v
```

### Project Structure

```
├── app.py                  # FastAPI server
├── engine.py               # Core decision tree logic
├── launcher.py             # Desktop app (WebView2 window)
├── updater.py              # GitHub release auto-updater
├── config.py               # Ports, paths, settings
├── data/
│   ├── rune_pages.py       # 10 rune page templates with perk IDs
│   ├── item_builds.py      # 16+ item build templates with item IDs
│   ├── matchup_table.py    # 71 matchups: enemy → keystones, difficulty
│   ├── rules.py            # IF-THEN adaptation rules
│   ├── role_rates.py       # Champion role classification
│   └── user_config.py      # Persistent user preferences
├── scrapers/
│   └── ddragon.py          # Data Dragon loader (icons, champion data)
├── lcu/                    # League Client integration
│   ├── client.py           # LCU API client
│   ├── champ_select.py     # Champ select tracker
│   ├── rune_import.py      # Import rune pages
│   ├── item_import.py      # Import item sets
│   ├── spell_import.py     # Import summoner spells
│   └── auto_detect.py      # Auto-detection coordinator
├── static/                 # Frontend (HTML/CSS/JS)
├── tests/
│   └── test_engine.py      # Engine + matchup tests
├── build.spec              # PyInstaller build config
├── installer.iss           # Inno Setup installer script
├── version_info.txt        # Windows exe version metadata
└── .github/workflows/
    └── release.yml         # CI/CD: build + release on tag push
```

## Releasing a New Version

1. Update the version number in three files:
   - `updater.py` → `APP_VERSION = "x.y.z"`
   - `version_info.txt` → `filevers` and `prodvers` tuples + version strings
   - `installer.iss` → `AppVersion=x.y.z`

2. Commit and tag:
   ```bash
   git add -A && git commit -m "Release vx.y.z"
   git tag vx.y.z
   git push origin master --tags
   ```

3. GitHub Actions automatically:
   - Builds the exe with PyInstaller
   - Creates the installer with Inno Setup
   - Publishes a GitHub Release with both files

4. Existing installations will show an "Update available!" banner on next launch.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health` | Server health check |
| `GET` | `/api/ddragon/champions` | Sorted champion list for dropdowns |
| `GET` | `/api/ddragon/version` | Current Data Dragon version |
| `POST` | `/api/build/query` | Query build for a single matchup |
| `POST` | `/api/build/query-multi` | Query build against full enemy team |
| `GET` | `/api/lcu/status` | LCU connection status |
| `POST` | `/api/lcu/import-runes` | Import rune page to League client |
| `POST` | `/api/lcu/import-items` | Import item set to League client |
| `POST` | `/api/lcu/import-spells` | Import summoner spells |
| `GET` | `/api/update/check` | Check for new release |
| `POST` | `/api/update/install` | Download and install update |

## Credits

- Build logic from [Kampsycho's Yorick Guide](https://docs.google.com/document/d/1AHaEfMCoSsyx3HpZmk2mEFnRiiwnB8CkGAYqzjhDJo/edit)
- Game data from [Data Dragon](https://developer.riotgames.com/docs/lol#data-dragon) and [Community Dragon](https://communitydragon.org/)
- Icons and assets are property of Riot Games

## License

MIT
