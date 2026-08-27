import sqlite3
from typing import List, Optional
from datetime import datetime
from .models import PromptModel

DEFAULT_PROMPTS = [
    {
        "name": "Humanize Text",
        "description": "Rewrite the following text so it sounds natural and human.",
        "category": "Writing",
        "template": "Rewrite the following text to sound natural and human while preserving the meaning.\n\nTEXT:\n{{text}}",
        "tags": "humanize,writing"
    },
    {
        "name": "Code Debugger",
        "description": "Analyze code, identify error, explain and fix.",
        "category": "Coding",
        "template": "Analyze this code, identify the error, explain why it happens, and provide a corrected version.\n\nCODE:\n{{code}}",
        "tags": "python,debug,code"
    },
    {
        "name": "SQL Helper",
        "description": "Write or optimize SQL queries.",
        "category": "Data",
        "template": "Write a SQL query for the following request.\n\nDatabase: {{db_type}}\nRequest: {{request}}",
        "tags": "sql,data"
    },
    {
        "name": "Interview Answer",
        "description": "Evaluate and improve an interview answer.",
        "category": "Interview",
        "template": "Evaluate this interview answer for the role of {{role}}. Provide constructive feedback and a better version.\n\nQuestion: {{question}}\nAnswer: {{answer}}",
        "tags": "interview,career"
    },
    {
        "name": "Image Customizer",
        "description": "Customize image generation prompt.",
        "category": "Images",
        "template": "Modify this image generation prompt according to the following instructions:\n\nPrompt: {{prompt}}\nInstructions: {{instructions}}",
        "tags": "image,prompt"
    }
]

class PromptManager:
    def __init__(self, db_conn: sqlite3.Connection):
        self.conn = db_conn
        self._seed_if_empty()

    def _seed_if_empty(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM prompts")
        if cursor.fetchone()[0] == 0:
            for p in DEFAULT_PROMPTS:
                self.add_prompt(PromptModel(
                    id=None,
                    name=p["name"],
                    description=p["description"],
                    category=p["category"],
                    template=p["template"],
                    tags=p["tags"],
                    favorite=False,
                    usage_count=0,
                    last_used=None
                ))

    def add_prompt(self, prompt: PromptModel) -> int:
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO prompts (
                name, description, category, template, tags, favorite, usage_count, last_used
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            prompt.name, prompt.description, prompt.category, prompt.template, 
            prompt.tags, prompt.favorite, prompt.usage_count, 
            prompt.last_used.isoformat() if prompt.last_used else None
        ))
        self.conn.commit()
        prompt.id = cursor.lastrowid
        return prompt.id

    def get_all(self) -> List[PromptModel]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name, description, category, template, tags, favorite, usage_count, last_used FROM prompts")
        
        results = []
        for row in cursor.fetchall():
            results.append(PromptModel(
                id=row[0],
                name=row[1],
                description=row[2],
                category=row[3],
                template=row[4],
                tags=row[5],
                favorite=bool(row[6]),
                usage_count=row[7],
                last_used=datetime.fromisoformat(row[8]) if row[8] else None
            ))
        return results

    def search(self, query: str) -> List[PromptModel]:
        all_prompts = self.get_all()
        q = query.lower()
        return [
            p for p in all_prompts
            if q in p.name.lower() or q in p.description.lower() or q in (p.tags or "").lower()
        ]

    def increment_usage(self, prompt_id: int):
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE prompts 
            SET usage_count = usage_count + 1, last_used = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (prompt_id,))
        self.conn.commit()
