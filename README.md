# CricImpact

CricImpact is a lightweight **Flask** web app that turns live cricket scorecards into clear, per-player **Impact** scores. It includes a live-match picker, per-match impact cards with symbols and tiers, and a floating “How it works” explainer so visitors immediately understand the math.

> Built to be simple to run locally, without any `.env`. If you have an API key, set it as a normal environment variable and you’ll get real live data. Otherwise, the app still runs with sample data for demos.

---

## 🌟 Features

- **Impact page** with a live-match picker and clean URLs: `/impact/<match_id>`  
- **Real-time metrics** when a scorecard is available (or graceful fallbacks when not)
- **Per-player cards** with:
  - ▲ / ▼ / ▬ symbols vs **team average**
  - **Tiers**: Elite, High, Solid, Developing
  - Batting vs Bowling breakdown
- **Floating “How it works” card** (bottom-right) that stays visible while you scroll
- **No `.env` required** — uses `CRICKET_API_KEY` if present
- **Seeded sample matches** so the UI isn’t empty on first run
- Clean, modular structure (`services/`, `impact/`, `templates/`, etc.)

---

## 🖼️ Screenshots

> These are stored under `screenshots/` in this repo. Filenames have spaces, so links below use `%20` encoding.

**Home**  
![CricImpact — Home](screenshots/CricImpact%20-%20HomePage.png)

**Impact Page (picker + cards)**  
![CricImpact — Impact Page](screenshots/CricImpact%20-%20ImpactPage.png)

**Impact Players (cards & tiers)**  
![CricImpact — Impact Players](screenshots/CricImpact%20-%20ImpactPlayers.png)

**How the Impact is calculated (explainer)**  
![CricImpact — Impact Calculation](screenshots/CricImpact%20-%20ImpactCalculation.png)

## 🧱 Tech Stack

- **Python 3.10+**
- **Flask** (+ Jinja2 templates)
- **Requests** (for API calls)
- HTML/CSS/JS (vanilla; works with Bootstrap-like styles if you add them)

---

## 📁 Project Structure

```
CricImpact/
├─ app.py
├─ requirements.txt
├─ templates/
│  ├─ layout.html
│  ├─ index.html
│  ├─ impact.html          # Impact page with live-match picker & floating help
│  ├─ live.html
│  ├─ live_detail.html
│  ├─ matches.html
│  └─ match_detail.html
├─ impact/
│  ├─ calculator.py        # Impact formulas & scorecard normalization
│  └─ sample_players.py
├─ services/
│  └─ cricket_api.py       # API helpers (match list, match details)
├─ scraper/
│  └─ fetch_scores.py      # Sample/local seed helpers
├─ db/
│  └─ models.py            # Lightweight SQLite helpers
├─ static/                 # (optional) images/css/js
└─ data/                   # (optional) local data (ignored by .gitignore)
```

> Make sure each package folder (`impact`, `services`, `scraper`, `db`) contains an empty `__init__.py` so Python can import them.

---

## 🚀 Quick Start

1) **Clone** and cd into the project folder.
2) **Install deps** (no virtualenv required, but recommended):
   ```bash
   pip install -r requirements.txt
   ```
3) **(Optional) Set your API key** if you have one:
   - **Windows (PowerShell)**  
     ```powershell
     setx CRICKET_API_KEY "your-api-key-here"
     ```
     _Restart the terminal/app after setting_
   - **macOS/Linux (for current shell)**  
     ```bash
     export CRICKET_API_KEY="your-api-key-here"
     ```
4) **Run it**:
   ```bash
   python app.py
   ```
5) **Open**: <http://127.0.0.1:5000/>

---

## 🔗 Useful Routes

- Home: `/`
- Live list: `/live`
- Impact: `/impact` (shows live-match chips)
- Impact for a specific match: `/impact/<match_id>`
- Matches (local/sample): `/matches`

> On the Impact page, **click a live match** to load `/impact/<match_id>`. If some live matches don’t show data, it usually means the scorecard isn’t available yet via the API — try another match.

---

## 🧮 How Impact Is Calculated

For each selected match, every player’s **Total Impact** is the sum of their batting and bowling impact.

### 1) Batting Impact
- Strike Rate `SR = (runs ÷ balls) × 100`
- **Bat Impact** = `runs × 0.4 + SR × 0.6`

### 2) Bowling Impact
- Overs like `4.3` mean 4 overs & 3 balls → `4 + 3/6 = 4.5`
- **Bowl Impact** = `wickets × 8 + (10 − overs_bowled)`

### 3) Total Impact
- **Total Impact** = `Bat Impact + Bowl Impact`

### 4) Symbols & Tiers
- **Symbols vs team average**:  
  - `▲` **above** team average (by more than 3)  
  - `▼` **below** team average (by more than −3)  
  - `▬` **near** team average (within ±3)
- **Tiers (by Total Impact)**:  
  - **Elite**: ≥ 110  
  - **High**: 80–109  
  - **Solid**: 50–79  
  - **Developing**: < 50

**Example**  
Batter: 60 (40) ⇒ SR = 150 → Bat = `60×0.4 + 150×0.6 = 114`  
Bowler: 2 wickets, 4.3 ov (4.5) → Bowl = `2×8 + (10−4.5) = 19.5`  
**Total = 133.5**

> The formulas are simple by design and easy to tweak in `impact/calculator.py`.

---

## ⚙️ Configuration

- **API key** (optional): set `CRICKET_API_KEY` to enable live data via the API.  
  Without it, the Impact page will still render with the UI and messaging, and other pages show sample/local data.
- **Local DB & data**: files under `data/` and `.sqlite` DBs are generally ignored via `.gitignore`.

---

## 🧪 Troubleshooting

- **Impact page says “No impact to show yet”**:  
  The selected match likely has **no public scorecard** yet. Try another live match (the app can also auto-pick the first match with a scorecard).
- **404 on `/impact/<id>`**:  
  Make sure you copied a valid `match_id` from the chips on `/impact`.
- **No API key**:  
  The app still runs; just fewer live details will be available.

---

## 🤝 Contributing

Issues and PRs are welcome. Typical flow:

```bash
git checkout -b feature/awesome-thing
# make changes
git add -A
git commit -m "Add awesome thing"
git push -u origin feature/awesome-thing
# Open a Pull Request on GitHub
```

---

## 📜 License

MIT — feel free to use and adapt. See `LICENSE` if you add one.

---

## 🙏 Acknowledgements

- Live data powered by your cricket API provider. This project is not affiliated with or endorsed by any governing body.
- Thanks to the open-source community for Flask and Python tools.
