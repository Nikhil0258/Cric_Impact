# app.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from flask import Flask, render_template, abort, request, redirect, url_for

# ---- Local modules (make sure each folder has an empty __init__.py) ----
from scraper.fetch_scores import get_sample_matches
from db.models import (
    init_db,
    insert_match,
    fetch_matches,
    get_match_by_id,
    insert_live_match,
)
from impact.sample_players import players as SAMPLE_PLAYERS
from impact.calculator import (
    calculate_batting_impact,
    calculate_bowling_impact,
    calculate_impact_for_match,
    summarize_impact,
)
from services.cricket_api import get_live_matches, get_match_details


# -----------------------------------------------------------------------------
# App bootstrap
# -----------------------------------------------------------------------------
app = Flask(__name__, template_folder="templates", static_folder="static")

# Ensure local data dir exists and DB is initialized
Path("data").mkdir(exist_ok=True)
init_db()


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def _seed_sample_matches() -> None:
    """Seed DB with sample matches if empty (so pages aren't blank on first run)."""
    if fetch_matches():
        return
    for m in get_sample_matches():
        m.setdefault("series", "")
        m.setdefault("venue", "")
        m.setdefault("date", "")
        m.setdefault("toss", "")
        m.setdefault("winner", "")
        insert_match(m)


_seed_sample_matches()


def _to_card(match: Dict[str, Any]) -> Dict[str, Any]:
    """Convert DB/sample match dict to the shape templates expect."""
    name = match.get("name") or f"{match.get('team1','')} vs {match.get('team2','')}".strip()
    return {
        "id": match.get("match_id") or match.get("id"),
        "name": name,
        "status": match.get("status", ""),
        "venue": match.get("venue", ""),
        "date": match.get("date", ""),
        "team1": match.get("team1", ""),
        "team2": match.get("team2", ""),
        "score": match.get("score", ""),
        "series": match.get("series", ""),
        "toss": match.get("toss", ""),
        "winner": match.get("winner", ""),
    }


def _impact_from_samples() -> List[Dict[str, Any]]:
    """Used by /players page (not for live impact)."""
    out: List[Dict[str, Any]] = []
    for p in SAMPLE_PLAYERS:
        bat = calculate_batting_impact(p["runs"], p["balls"])
        bowl = calculate_bowling_impact(p["wickets"], p["overs"])
        total = round(bat + bowl, 2)
        role = "All-rounder" if (p["wickets"] and p["runs"] >= 20) else ("Bowler" if p["wickets"] else "Batter")
        out.append(
            {
                "name": p["name"],
                "team": p.get("team", ""),
                "role": role,
                "impact_score": total,
                "runs": p["runs"],
                "balls": p["balls"],
                "wickets": p["wickets"],
                "overs": p["overs"],
                "total_impact": total,
            }
        )
    return out


# -------- scorecard helpers (to improve UX when some matches lack a card) ----
_SCORECARD_KEYS = ("scorecard", "scoreCard", "Scorecard", "innings", "scorecards", "scoreCards")


def _scorecard_exists(details: Optional[Dict[str, Any]]) -> bool:
    """Return True if details contains a scorecard list (in any common shape)."""
    if not isinstance(details, dict):
        return False

    def has_list(container: Any, key: str) -> bool:
        if not isinstance(container, dict):
            return False
        v = container.get(key)
        if isinstance(v, list) and len(v) > 0:
            return True
        if isinstance(v, dict) and isinstance(v.get("innings"), list) and v["innings"]:
            return True
        return False

    # direct keys
    for k in _SCORECARD_KEYS:
        if has_list(details, k):
            return True

    # one level nested
    for v in details.values():
        if isinstance(v, dict):
            for k in _SCORECARD_KEYS:
                if has_list(v, k):
                    return True

    return False


def _first_live_with_scorecard(live_matches: List[Dict[str, Any]]) -> Optional[str]:
    """Return the first match id in the list that has a scorecard."""
    for m in live_matches:
        mid = m.get("id")
        if not mid:
            continue
        d = get_match_details(mid)
        if _scorecard_exists(d):
            return mid
    return None


# ---------------- Impact page renderer (used by /impact and /impact/<id>) ----------------
def _render_impact(match_id: Optional[str]):
    """
    Renders the Impact page.
    - Always shows a list of live matches (chips).
    - If match_id is provided, computes and shows per-player impact.
    - If that match has no scorecard, show a friendly note.
    """
    live = get_live_matches()  # [] if no API key or no current matches

    impact_players: List[Dict[str, Any]] = []
    impact_summary: Optional[Dict[str, Any]] = None
    impact_note: Optional[str] = None

    if match_id:
        impact_players = calculate_impact_for_match(match_id) or []
        if not impact_players:
            # Give a specific reason if we can detect it
            details = get_match_details(match_id)
            if not _scorecard_exists(details):
                status = (details or {}).get("status") or ""
                impact_note = "No scorecard is available for this match yet. Try another live match."
                if status:
                    impact_note += f" (status: {status})"
            else:
                impact_note = "Scorecard found but couldn’t be parsed. Try a different match."
        else:
            impact_summary = summarize_impact(impact_players)

    return render_template(
        "impact.html",
        live_matches=live,            # chips at the top
        active_match_id=match_id,     # highlight selected chip
        impact_players=impact_players,
        impact_summary=impact_summary,
        impact_note=impact_note,      # explain why it's empty when selected
    )


# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------
@app.route("/")
def index():
    live = get_live_matches()[:4]  # [] when no API key set
    saved = [_to_card(m) for m in fetch_matches()][:4]
    trending_series = [{"name": m["series"]} for m in fetch_matches() if m.get("series")] or []
    return render_template("index.html",
                           live_matches=live,
                           matches=saved,
                           trending_series=trending_series[:6])


@app.route("/matches")
def show_matches():
    matches = [_to_card(m) for m in fetch_matches()]
    return render_template("matches.html", matches=matches)


@app.route("/matches/<match_id>")
def show_match_detail(match_id: str):
    # Try DB, then the bundled samples
    m = get_match_by_id(match_id) or next((x for x in get_sample_matches() if x["match_id"] == match_id), None)
    if not m:
        abort(404)

    status_text = (m.get("status") or "").lower()
    status_color = "red" if "live" in status_text else ("green" if "won" in status_text or "finished" in status_text else "inherit")

    # Optional: per-match impact on detail page
    impact_data = calculate_impact_for_match(match_id) or []

    return render_template("match_detail.html",
                           match={**m, "status_color": status_color},
                           impact_data=impact_data)


@app.route("/live")
def show_live_matches():
    matches = get_live_matches()
    return render_template("live.html", matches=matches)


@app.route("/live/<match_id>")
def show_live_match_detail(match_id: str):
    match = get_match_details(match_id)
    if not match:
        abort(404)
    return render_template("live_detail.html", match=match)


@app.route("/store-live")
def store_live_matches():
    """Dev helper to copy current API matches into your local DB."""
    matches = get_live_matches()
    count = 0
    for m in matches:
        try:
            insert_live_match(m)
            count += 1
        except Exception:
            pass  # ignore duplicates
    return f"✅ Stored {count} matches from API."


@app.route("/players")
def show_players():
    return render_template("players.html", players=_impact_from_samples())


# --- Impact: supports both /impact and /impact/<match_id> ---
@app.route("/impact")
def show_impact():
    # Auto-pick the first live match that actually has a scorecard
    live = get_live_matches()
    auto = _first_live_with_scorecard(live)
    if auto:
        return redirect(url_for("show_impact_match", match_id=auto))
    # Otherwise show the chooser with a friendly empty state
    return _render_impact(None)


@app.route("/impact/<match_id>")
def show_impact_match(match_id: str):
    return _render_impact(match_id)


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    # Optional: if you have an API key, set it as a normal OS env var:
    #   Windows (PowerShell):  setx CRICKET_API_KEY "your-key"
    #   macOS/Linux (shell):   export CRICKET_API_KEY="your-key"
    app.run(debug=True)
