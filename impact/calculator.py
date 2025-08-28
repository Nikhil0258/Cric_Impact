from __future__ import annotations

from typing import Any, Dict, List, Optional

try:
    from services.cricket_api import get_match_details
except Exception:  # pragma: no cover
    get_match_details = None  # type: ignore


# ---------------- Basic impact formulas ----------------
def calculate_batting_impact(runs: float, balls: float) -> float:
    runs = float(runs or 0)
    balls = float(balls or 0)
    sr = (runs / balls) * 100 if balls > 0 else 0.0
    return round((runs * 0.4) + (sr * 0.6), 2)


def calculate_bowling_impact(wickets: float, overs: float) -> float:
    wickets = float(wickets or 0)
    overs = float(overs or 0)
    return round((wickets * 8) + (10 - overs), 2)


# ---------------- Helpers ----------------
def _i(x: Any) -> int:
    try:
        return int(str(x).strip())
    except Exception:
        return 0


def _f(x: Any) -> float:
    try:
        return float(str(x).strip())
    except Exception:
        return 0.0


def _overs_to_float(ov: Any) -> float:
    # Accept "4.3" => 4.5, or numeric
    if ov is None:
        return 0.0
    if isinstance(ov, (int, float)):
        return float(ov)
    s = str(ov)
    if "." in s:
        whole, balls_s = s.split(".", 1)
        balls = min(_i("".join(ch for ch in balls_s if ch.isdigit()) or "0"), 6)
        return _i(whole) + balls / 6.0
    return _f(s)


def _pick(d: Dict[str, Any], keys: List[str], default: Any = None) -> Any:
    for k in keys:
        if k in d and d[k] not in (None, ""):
            return d[k]
    return default


def _team_name(val: Any) -> str:
    """Normalize a team value (dict/list/str) to a clean string."""
    if isinstance(val, dict):
        return str(val.get("name") or val.get("teamName") or val.get("shortName") or val.get("abbr") or "")
    if isinstance(val, list):
        names = []
        for v in val:
            n = _team_name(v)
            if n and n not in names:
                names.append(n)
        return " / ".join(names)
    return str(val or "")


def _player_name(val: Any) -> str:
    """Normalize a player reference (dict/str/int) to a displayable string."""
    if isinstance(val, dict):
        return str(
            val.get("name")
            or val.get("fullName")
            or val.get("playerName")
            or val.get("shortName")
            or val.get("batsman")
            or val.get("bowler")
            or val.get("id")
            or ""
        )
    return str(val or "")


# ---------------- Scorecard extraction ----------------
def _extract_scorecards(details: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Accept multiple shapes:
    - details['scorecard'] OR 'scoreCard' (list of innings dicts)
    - details['innings'] (some APIs return directly)
    - details['scorecards'] (alt plural)
    - nested dicts that contain one of the above
    """
    for k in ("scorecard", "scoreCard", "Scorecard", "innings", "scorecards", "scoreCards"):
        sc = details.get(k)
        if isinstance(sc, list) and sc:
            return sc

    # Sometimes nested one level deeper
    for v in details.values():
        if isinstance(v, dict):
            for k in ("scorecard", "scoreCard", "Scorecard", "innings", "scorecards", "scoreCards"):
                sc = v.get(k)
                if isinstance(sc, list) and sc:
                    return sc

    return []


def _combine(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(a)
    for k, v in b.items():
        if k in ("runs", "balls", "wickets", "overs"):
            out[k] = out.get(k, 0) + v
        elif k == "team":
            v = _team_name(v)
            if not out.get(k):
                out[k] = v
        elif k == "name":
            v = _player_name(v)
            if not out.get(k):
                out[k] = v
    return out


def _normalize_from_scorecard(scorecard: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Collapse a scorecard into per-player stats.

    Understands keys:
      batting blocks: 'batting' or 'batsmen'
        - name: 'batsman'/'batter'/'name'/'playerName' (can be dict!)
        - runs: 'runs'/'R'/'r'
        - balls: 'balls'/'B'/'b'
      bowling blocks: 'bowling' or 'bowlers'
        - name: 'bowler'/'name'/'playerName' (can be dict!)
        - overs: 'overs'/'O'/'o'
        - wickets: 'wickets'/'W'/'w'
    """
    players: Dict[str, Dict[str, Any]] = {}

    for inn in scorecard or []:
        batting_team = _team_name(_pick(inn, ["batTeamName", "team", "teamName"], ""))

        # ---- batting rows ----
        bat_block = inn.get("batting") or inn.get("batsmen") or []
        if isinstance(bat_block, dict):
            bat_block = list(bat_block.values())
        for bt in bat_block or []:
            if not isinstance(bt, dict):
                continue
            raw_name = _pick(bt, ["batsman", "batter", "name", "playerName"], "")
            name = _player_name(raw_name)
            if not name:
                continue
            runs = _i(_pick(bt, ["runs", "R", "r"], 0))
            balls = _i(_pick(bt, ["balls", "B", "b"], 0))
            entry = {"name": name, "team": batting_team, "runs": runs, "balls": balls, "wickets": 0, "overs": 0.0}
            key = f"{batting_team}::{name}"   # key is ALWAYS a string
            players[key] = _combine(players.get(key, {}), entry)

        # ---- bowling rows ----
        bowl_block = inn.get("bowling") or inn.get("bowlers") or []
        if isinstance(bowl_block, dict):
            bowl_block = list(bowl_block.values())
        for bl in bowl_block or []:
            if not isinstance(bl, dict):
                continue
            raw_name = _pick(bl, ["bowler", "name", "playerName"], "")
            name = _player_name(raw_name)
            if not name:
                continue
            wickets = _i(_pick(bl, ["wickets", "W", "w"], 0))
            overs = _overs_to_float(_pick(bl, ["overs", "O", "o"], 0))
            bowl_team = _team_name(_pick(bl, ["teamName", "team"], ""))  # sometimes present
            entry = {"name": name, "team": bowl_team, "runs": 0, "balls": 0, "wickets": wickets, "overs": overs}
            key = f"{bowl_team}::{name}"
            players[key] = _combine(players.get(key, {}), entry)

    return players


# ---------------- Public API ----------------
def calculate_impact_for_match(match_id: str) -> List[Dict[str, Any]]:
    """Compute per-player impact from the most tolerant read of the scorecard."""
    if not match_id or get_match_details is None:
        return []

    details = get_match_details(match_id)
    if not details:
        return []

    scorecard = _extract_scorecards(details)
    if not scorecard:
        return []  # no card available yet

    people = _normalize_from_scorecard(scorecard)

    out: List[Dict[str, Any]] = []
    for p in people.values():
        bat = calculate_batting_impact(p.get("runs", 0), p.get("balls", 0))
        bowl = calculate_bowling_impact(p.get("wickets", 0), p.get("overs", 0.0))
        total = round(bat + bowl, 2)
        role = "All-rounder" if (p.get("wickets", 0) and p.get("runs", 0) >= 20) else \
               ("Bowler" if p.get("wickets", 0) else "Batter")
        out.append({
            "name": _player_name(p.get("name", "")),
            "team": _team_name(p.get("team", "")),
            "role": role,
            "impact_score": total,
            "bat_impact": bat,
            "bowl_impact": bowl,
            "runs": p.get("runs", 0),
            "balls": p.get("balls", 0),
            "wickets": p.get("wickets", 0),
            "overs": p.get("overs", 0.0),
        })

    _annotate_with_team_stats(out)
    out.sort(key=lambda x: x["impact_score"], reverse=True)
    return out


def summarize_impact(players: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not players:
        return {"count": 0, "global_avg": 0.0, "team_avgs": {}}
    team_sum: Dict[str, float] = {}
    team_cnt: Dict[str, int] = {}
    for p in players:
        t = _team_name(p.get("team", ""))  # force string
        team_sum[t] = team_sum.get(t, 0.0) + p["impact_score"]
        team_cnt[t] = team_cnt.get(t, 0) + 1
    team_avgs = {t: round(team_sum[t] / team_cnt[t], 2) for t in team_sum}
    global_avg = round(sum(p["impact_score"] for p in players) / len(players), 2)
    best = max(players, key=lambda x: x["impact_score"])
    worst = min(players, key=lambda x: x["impact_score"])
    return {"count": len(players), "global_avg": global_avg, "team_avgs": team_avgs,
            "best": {"name": best["name"], "score": best["impact_score"]},
            "worst": {"name": worst["name"], "score": worst["impact_score"]}}


def _annotate_with_team_stats(players: List[Dict[str, Any]]) -> None:
    if not players:
        return
    sums, counts = {}, {}
    for p in players:
        t = _team_name(p.get("team", ""))  # ALWAYS a string
        sums[t] = sums.get(t, 0.0) + p["impact_score"]
        counts[t] = counts.get(t, 0) + 1
    team_avg = {t: (sums[t] / counts[t]) for t in sums}

    def tier(score: float) -> str:
        if score >= 110: return "elite"
        if score >= 80:  return "high"
        if score >= 50:  return "solid"
        return "developing"

    for p in players:
        t = _team_name(p.get("team", ""))
        avg = team_avg.get(t, 0.0)
        delta = round(p["impact_score"] - avg, 2) if avg > 0 else 0.0
        pct = round((delta / avg) * 100, 1) if avg > 0 else 0.0
        sym = "▲" if delta > 3 else ("▼" if delta < -3 else "▬")
        p["tier"] = tier(p["impact_score"])
        p["delta_team"] = delta
        p["pct_vs_team"] = pct
        p["symbol"] = sym
