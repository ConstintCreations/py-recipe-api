from fastapi import FastAPI, HTTPException, Depends, Header, Request, BackgroundTasks
from pydantic import BaseModel
import secrets
import sqlite3
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import requests
from PIL import Image
import os
from io import BytesIO

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
        instructions TEXT NOT NULL,
        image_url TEXT,
        image_file_path TEXT,
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
    instructions: str
    is_public: bool = True
    image_url: str | None = None

class UpdateName(BaseModel):
    name: str

def create_api_key(username: str) -> str:
    try:
        key = secrets.token_hex(16)
        cursor.execute("INSERT INTO users (username, api_key) VALUES (?, ?)", (username, key))
        conn.commit()
        return key
    except Exception:
        raise HTTPException(status_code=400, detail="User already exists")

async def verify_api_key(x_api_key: str = Header()):
    cursor.execute("SELECT * FROM users WHERE api_key = ?", (x_api_key,))
    result = cursor.fetchone()
    if result is None:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return result

def get_api_key(request: Request) -> str:
    return request.headers.get("x-api-key", "unknown")

limiter = Limiter(key_func=get_api_key)
app.state.limiter = limiter

def process_image(recipe_id: int, image_url: str):
    try:
        print(f"Processing Image at ID {recipe_id}")
        connBg = sqlite3.connect("recipes.db")
        cursorBg = connBg.cursor()

        response = requests.get(image_url, timeout=10)

        if response.status_code != 200 or "image" not in response.headers.get("content-type", ""):
            return
        
        image = Image.open(BytesIO(response.content))
        
        image.thumbnail((1000, 1000))

        os.makedirs("images", exist_ok=True)
        image = image.convert("RGB")
        image_file_path = f"images/image_{recipe_id}.webp"
        image.save(image_file_path, "WEBP", quality=75)

        cursorBg.execute("UPDATE recipes SET image_file_path = ? WHERE id = ?", (image_file_path, recipe_id))

        connBg.commit()
        connBg.close()
        print(f"Image Processed at ID {recipe_id}")
    except Exception as e:
        print("Image Processing Failed: ", e)
        return
    
app.mount("/images", StaticFiles(directory="images"), name="images")

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded. Try again later!"}
    )

@app.post("/register")
async def register(body: RegisterBody):
    key = create_api_key(body.name)
    return {"api_key": key, "message": "This is your API key. Save it somewhere! You won't be able to see it again."}

@app.post("/recipes")
@limiter.limit("5/minute")
async def create_recipe(request: Request, body: Recipe, background_tasks: BackgroundTasks, key_info = Depends(verify_api_key)):

    user_id = key_info[0]

    public = int(body.is_public)

    cursor.execute(
        "INSERT INTO recipes (title, description, ingredients, instructions, image_url, is_public, user_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            body.title,
            body.description,
            body.ingredients,
            body.instructions,
            body.image_url,
            public,
            user_id
        )
    )

    conn.commit()

    recipe_id = cursor.lastrowid

    if body.image_url:
        background_tasks.add_task(process_image, recipe_id, body.image_url)

    return {"message": "Recipe Created!", "recipe_id": recipe_id}

@app.get("/recipes/public")
async def get_public_recipes(request: Request, page:int = 1, max_per_page:int = 50):
    if max_per_page > 200 or max_per_page <= 0:
        max_per_page = 50
    if page <= 0:
        page = 1
    
    offset = (page - 1) * max_per_page

    cursor.execute("""
    SELECT recipes.id, title, description, ingredients, instructions, image_file_path, user_id, users.username 
    FROM recipes
    JOIN users ON recipes.user_id = users.id
    WHERE recipes.is_public = 1 
    ORDER BY recipes.id DESC
    LIMIT ? OFFSET ?
    """, (max_per_page, offset))

    rows = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) FROM recipes WHERE is_public = 1")
    total = cursor.fetchone()[0]

    base_url = str(request.base_url)

    return {
        "page": page,
        "count": len(rows),
        "total": total,
        "recipes": [{
            "id": row[0],
            "title": row[1],
            "description": row[2],
            "ingredients": row[3],
            "instructions": row[4],
            **({"image_url": f"{base_url}{row[5]}"} if row[5] else {}),
            "user": {
                "user_id": row[6],
                "username": row[7]
            }

        } for row in rows ]
    }

@app.patch("/user/name")
@limiter.limit("2/hour")
async def change_name(request: Request, body:UpdateName, key_info = Depends(verify_api_key)):
    user_id = key_info[0]

    cursor.execute("UPDATE users SET username = ? WHERE id = ?", (body.name, user_id))
    conn.commit()

    return {"message": f"Username updated to {body.name}"}

@app.delete("/user")
async def delete_user(key_info = Depends(verify_api_key)):
    user_id = key_info[0]

    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()

    return {"message": f"User Deleted"}