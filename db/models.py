import sqlite3

DB_PATH = "data/matches.sqlite"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Drop old matches table if it exists (clean reset)
    cursor.execute("DROP TABLE IF EXISTS matches")

    # Recreate match table with extended fields
    cursor.execute('''
    CREATE TABLE matches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        match_id TEXT,
        team1 TEXT,
        team2 TEXT,
        status TEXT,
        score TEXT,
        series TEXT,
        venue TEXT,
        date TEXT,
        toss TEXT,
        winner TEXT
    )
    ''')

    # Create player table (leave as-is if you're already using it)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS players (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        match_id TEXT,
        name TEXT,
        runs INTEGER,
        balls INTEGER,
        wickets INTEGER,
        overs REAL,
        impact_score REAL
    )
    ''')

    conn.commit()
    conn.close()
    print("✅ Database created with updated schema.")


def insert_match(match):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT 1 FROM matches WHERE match_id = ?", (match['match_id'],))
    exists = cursor.fetchone()

    if not exists:
        cursor.execute('''
            INSERT INTO matches (match_id, team1, team2, status, score, series, venue, date, toss, winner)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            match['match_id'], match['team1'], match['team2'], match['status'], match['score'],
            match.get('series', ''), match.get('venue', ''), match.get('date', ''), 
            match.get('toss', ''), match.get('winner', '')
        ))
        conn.commit()

    conn.close()

def fetch_matches():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT match_id, team1, team2, status, score FROM matches")
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "match_id": row[0],
            "team1": row[1],
            "team2": row[2],
            "status": row[3],
            "score": row[4]
        } for row in rows
    ]

def get_match_by_id(match_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT match_id, team1, team2, status, score, series, venue, date, toss, winner
        FROM matches
        WHERE match_id = ?
    """, (match_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "match_id": row[0],
            "team1": row[1],
            "team2": row[2],
            "status": row[3],
            "score": row[4],
            "series": row[5],
            "venue": row[6],
            "date": row[7],
            "toss": row[8],
            "winner": row[9]
        }
    else:
        return None

def clear_matches():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM matches")
    conn.commit()
    conn.close()

def get_match_by_id(match_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT match_id, team1, team2, status, score, series, venue, date, toss, winner
        FROM matches
        WHERE match_id = ?
    """, (match_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "match_id": row[0],
            "team1": row[1],
            "team2": row[2],
            "status": row[3],
            "score": row[4],
            "series": row[5],
            "venue": row[6],
            "date": row[7],
            "toss": row[8],
            "winner": row[9]
        }
    else:
        return None

def insert_live_match(match):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT 1 FROM matches WHERE match_id = ?", (match['id'],))
    exists = cursor.fetchone()

    if not exists:
        cursor.execute('''
            INSERT INTO matches (match_id, team1, team2, status, score, series, venue, date, toss, winner)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            match['id'],
            match['teams'][0] if match.get('teams') else '',
            match['teams'][1] if match.get('teams') else '',
            match.get('status', ''),
            '',  # Placeholder score
            match.get('name', ''),
            match.get('venue', ''),
            match.get('date', ''),
            match.get('tossWinner', ''),
            match.get('matchWinner', '')
        ))
        conn.commit()

    conn.close()
