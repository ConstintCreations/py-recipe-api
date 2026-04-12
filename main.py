from fastapi import FastAPI, HTTPException, Depends, Header, Request
from pydantic import BaseModel
import secrets
import sqlite3
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse

app = FastAPI()

conn = sqlite3.connect("recipes.db")
cursor = conn.cursor()

conn.execute("PRAGMA foreign_keys = ON")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        api_key TEXT UNIQUE NOT NULL
    )
"""
)

cursor.execute("""
    CREATE TABLE IF NOT EXISTS recipes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        ingredients TEXT NOT NULL,
        image_url TEXT,
        user_id INTEGER NOT NULL,

        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    )
"""    
)

conn.commit()

class RegisterBody(BaseModel):
    name: str

def create_api_key(username: str) -> str:
    key = secrets.token_hex(16)
    cursor.execute(
        "INSERT INTO users (username, api_key) VALUES (?, ?)",
        (username, key)
    )
    conn.commit()
    return key

@app.post("/register")
async def register(body: RegisterBody):
    key = create_api_key(body.name)
    return {"api_key": key, "message": "This is your API key. Save it somewhere! You won't be able to see it again."}