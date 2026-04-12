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
        is_public INTEGER NOT NULL DEFAULT 1,

        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    )
"""    
)

conn.commit()

class RegisterBody(BaseModel):
    name: str

class Recipe(BaseModel):
    title: str
    description: str | None = None
    ingredients: str
    is_public: bool = True
    image_url: str | None = None

def create_api_key(username: str) -> str:
    key = secrets.token_hex(16)
    cursor.execute("INSERT INTO users (username, api_key) VALUES (?, ?)", (username, key))
    conn.commit()
    return key

async def verify_api_key(x_api_key: str = Header()):
    cursor.execute("SELECT * FROM users WHERE api_key = ?", (x_api_key,))
    result = cursor.fetchone()
    if result is None:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return result

@app.post("/register")
async def register(body: RegisterBody):
    key = create_api_key(body.name)
    return {"api_key": key, "message": "This is your API key. Save it somewhere! You won't be able to see it again."}

@app.post("/recipes")
async def create_recipe(body: Recipe, key_info = Depends(verify_api_key)):

    user_id = key_info[0]

    public = int(body.is_public)

    cursor.execute(
        "INSERT INTO recipes (title, description, ingredients, image_url, is_public, user_id) VALUES (?, ?, ?, ?, ?, ?)",
        (
            body.title,
            body.description,
            body.ingredients,
            body.image_url,
            public,
            user_id
        )
    )

    conn.commit()

    recipe_id = cursor.lastrowid

    return {"message": "Recipe Created!", "recipe_id": recipe_id}