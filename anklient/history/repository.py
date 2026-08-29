import sqlite3
from datetime import datetime

from .models import HistoryItem


class HistoryRepository:
    def __init__(self, db_conn: sqlite3.Connection):
        self.conn = db_conn

    def save(self, item: HistoryItem) -> int:
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO history (
                timestamp, prompt, response, category, ttft_ms, total_ms, word_count, char_count, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item.timestamp.isoformat(),
            item.prompt,
            item.response,
            item.category,
            item.ttft_ms,
            item.total_ms,
            item.word_count,
            item.char_count,
            item.status
        ))
        self.conn.commit()
        item.id = cursor.lastrowid
        return item.id

    def get_recent(self, limit: int = 10) -> list[HistoryItem]:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, timestamp, prompt, response, category, ttft_ms, total_ms, word_count, char_count, status
            FROM history
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        results = []
        for row in cursor.fetchall():
            results.append(HistoryItem(
                id=row[0],
                timestamp=datetime.fromisoformat(row[1]),
                prompt=row[2],
                response=row[3],
                category=row[4],
                ttft_ms=row[5],
                total_ms=row[6],
                word_count=row[7],
                char_count=row[8],
                status=row[9]
            ))
        return results

    def clear(self):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM history")
        self.conn.commit()
