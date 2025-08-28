from __future__ import annotations

import os
import requests
from typing import Any, Dict, List, Optional

API_KEY = os.getenv("CRICKET_API_KEY")  # optional
BASE_URL = "https://api.cricapi.com/v1"


def _request(path: str, **params) -> Optional[dict]:
    """Call CricAPI and return parsed JSON, or None if unavailable."""
    if not API_KEY:
        return None
    url = f"{BASE_URL}/{path}"
    params = {"apikey": API_KEY, **params}
    try:
        r = requests.get(url, params=params, timeout=12)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def get_live_matches() -> List[Dict[str, Any]]:
    """Return normalized list of current matches. Empty list if no key/error."""
    payload = _request("currentMatches", offset=0)
    if not payload or payload.get("status") != "success":
        return []

    out: List[Dict[str, Any]] = []
    for m in payload.get("data", []) or []:
        teams = m.get("teams") or []
        if not teams and m.get("teamInfo"):
            teams = [ti.get("name", "") for ti in m.get("teamInfo", [])]
        name = m.get("name") or (" vs ".join([t for t in teams if t]) or "Match")
        out.append({
            "id": m.get("id") or m.get("unique_id") or name,
            "name": name,
            "status": m.get("status", ""),
            "teams": teams,
            "venue": m.get("venue", ""),
            "date": m.get("date") or m.get("dateTimeGMT") or "",
            "tossWinner": m.get("tossWinner"),
            "matchWinner": m.get("matchWinner"),
        })
    return out


def get_match_details(match_id: str) -> Optional[Dict[str, Any]]:
    """
    Return detailed info for a specific match id, trying multiple endpoints and
    merging results so that 'scorecard' exists when available.
    """
    data: Dict[str, Any] = {}

    # 1) Try match_info
    p1 = _request("match_info", id=match_id)
    if p1 and p1.get("status") == "success":
        d1 = p1.get("data") or {}
        if isinstance(d1, dict):
            data.update(d1)

    # 2) If scorecard not present, try match_scorecard
    if not any(k in data for k in ("scorecard", "scoreCard", "Scorecard", "innings", "scorecards", "scoreCards")):
        p2 = _request("match_scorecard", id=match_id)
        if p2 and p2.get("status") == "success":
            d2 = p2.get("data") or {}
            if isinstance(d2, dict):
                # prefer explicit scorecard keys from d2, but keep names/teams from d1
                data = {**data, **d2}

    # Normalize some top-level fields
    teams = data.get("teams") or []
    if not teams and data.get("teamInfo"):
        teams = [ti.get("name", "") for ti in data.get("teamInfo", [])]
        data["teams"] = teams
    if not data.get("name"):
        data["name"] = " vs ".join([t for t in teams if t]) or "Match"

    return data or None
