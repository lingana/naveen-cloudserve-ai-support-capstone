import sqlite3
from pathlib import Path

SCHEMA = '''CREATE TABLE IF NOT EXISTS decisions (
 decision_id TEXT PRIMARY KEY, created_at TEXT NOT NULL, ticket_id TEXT NOT NULL,
 stage TEXT NOT NULL, prediction TEXT, confidence REAL, threshold REAL,
 action_taken TEXT NOT NULL, reason TEXT NOT NULL, sources_used TEXT,
 guardrails TEXT, prompt_version TEXT, requirement_ids TEXT
)'''

class DecisionStore:
    def __init__(self, db_path: str = "./storage/decisions.db"):
        if db_path.startswith("sqlite:///"):
            db_path = db_path.replace("sqlite:///", "", 1)
        self.path = Path(db_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as con:
            con.execute(SCHEMA)

    def add(self, decision: dict):
        with sqlite3.connect(self.path) as con:
            con.execute('''INSERT OR REPLACE INTO decisions
            (decision_id,created_at,ticket_id,stage,prediction,confidence,threshold,
             action_taken,reason,sources_used,guardrails,prompt_version,requirement_ids)
            VALUES (:decision_id,:created_at,:ticket_id,:stage,:prediction,:confidence,:threshold,
             :action_taken,:reason,:sources_used,:guardrails,:prompt_version,:requirement_ids)''', decision)

    def count(self):
        with sqlite3.connect(self.path) as con:
            return con.execute("SELECT COUNT(*) FROM decisions").fetchone()[0]
