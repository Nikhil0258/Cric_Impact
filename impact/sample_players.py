players = [
    {"name": "Virat Kohli", "runs": 85, "balls": 64, "wickets": 0, "overs": 0},
    {"name": "Bumrah", "runs": 5, "balls": 8, "wickets": 3, "overs": 10},
    {"name": "Ben Stokes", "runs": 45, "balls": 31, "wickets": 1, "overs": 6}
]
def get_sample_matches():
    return [
        {
            "match_id": "match_001",
            "team1": "India",
            "team2": "England",
            "score": "IND 287/4 (47.3), ENG 284/9 (50)",
            "status": "India won by 6 wickets",
            "series": "India tour of England, 2025",
            "venue": "Kennington Oval, London",
            "date": "Aug 04, 2025",
            "toss": "England (Bowling)",
            "winner": "India"
        },
        {
            "match_id": "match_002",
            "team1": "Australia",
            "team2": "Pakistan",
            "score": "AUS 150/2 (25)",
            "status": "Live",
            "series": "Pakistan tour of Australia, 2025",
            "venue": "MCG, Melbourne",
            "date": "Aug 06, 2025",
            "toss": "Australia (Batting)",
            "winner": ""
        }
    ]
