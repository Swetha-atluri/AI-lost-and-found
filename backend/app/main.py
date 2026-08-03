import os
import shutil
import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from sqlalchemy.orm import Session

from backend.app.config import UPLOAD_DIR, MOCK_EMAIL_DIR
from backend.app.database import engine, Base, get_db, User, LostItem, FoundItem, Match
from backend.app.auth import get_current_user, create_access_token, verify_password
from backend.app import crud, schemas
from backend.app.ai_engine import ai_engine

# Initialize database tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Lost & Found Assistant API", version="1.0.0")

# Setup CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For demo purposes, permit all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create folders if not exists
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(MOCK_EMAIL_DIR, exist_ok=True)

# Helper function to save upload file
def save_upload_file(upload_file: UploadFile) -> str:
    # Generate unique filename to avoid collisions
    ext = os.path.splitext(upload_file.filename)[1]
    filename = f"{uuid.uuid4()}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    # Return path relative to the backend project root to serve it easily
    return f"backend/uploads/{filename}"


# --- AUTH ROUTES ---

@app.post("/api/auth/register", response_model=schemas.UserResponse)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user_username = crud.get_user_by_username(db, user.username)
    if db_user_username:
        raise HTTPException(status_code=400, detail="Username already registered")
    db_user_email = crud.get_user_by_email(db, user.email)
    if db_user_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db, user)

@app.post("/api/auth/login", response_model=schemas.Token)
def login(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = crud.get_user_by_username(db, username)
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/auth/me", response_model=schemas.UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


# --- LOST ITEMS ROUTES ---

@app.post("/api/items/lost", response_model=schemas.LostItemResponse)
async def create_lost_item(
    name: str = Form(...),
    category: str = Form(...),
    description: str = Form(...),
    date_lost: str = Form(...),
    location: str = Form(...),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Parse date
    try:
        # Expecting ISO string e.g. "2026-08-03T11:00:00"
        dt = datetime.fromisoformat(date_lost.replace("Z", ""))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use ISO format.")
        
    image_path = None
    if image and image.filename:
        image_path = save_upload_file(image)
        
    item_create = schemas.LostItemCreate(
        name=name, category=category, description=description, date_lost=dt, location=location
    )
    
    db_item = crud.create_lost_item(db, item_create, current_user.id, image_path)
    
    # Dynamically feed this item into the AI engine index
    try:
        ai_engine.add_lost_item(db_item)
    except Exception as e:
        print(f"[AI ENGINE WARNING] Failed to add item to live index: {e}")
        
    return db_item

@app.get("/api/items/lost", response_model=List[schemas.LostItemResponse])
def get_lost_items(db: Session = Depends(get_db)):
    return crud.get_lost_items(db)

@app.get("/api/items/lost/my", response_model=List[schemas.LostItemResponse])
def get_my_lost_items(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return crud.get_user_lost_items(db, current_user.id)


# --- FOUND ITEMS ROUTES ---

@app.post("/api/items/found", response_model=schemas.FoundItemResponse)
async def create_found_item(
    description: str = Form(...),
    date_found: str = Form(...),
    location: str = Form(...),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        dt = datetime.fromisoformat(date_found.replace("Z", ""))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use ISO format.")
        
    image_path = None
    if image and image.filename:
        image_path = save_upload_file(image)
        
    item_create = schemas.FoundItemCreate(
        description=description, date_found=dt, location=location
    )
    
    db_item = crud.create_found_item(db, item_create, current_user.id, image_path)
    
    # Trigger matching engine check for this newly uploaded found item
    try:
        ai_engine.check_matches_for_found_item(db_item, db)
    except Exception as e:
        print(f"[AI ENGINE WARNING] Match checking encountered an error: {e}")
        
    return db_item

@app.get("/api/items/found", response_model=List[schemas.FoundItemResponse])
def get_found_items(db: Session = Depends(get_db)):
    return crud.get_found_items(db)

@app.get("/api/items/found/my", response_model=List[schemas.FoundItemResponse])
def get_my_found_items(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return crud.get_user_found_items(db, current_user.id)


# --- MATCHES ROUTES ---

@app.get("/api/matches", response_model=List[schemas.MatchResponse])
def get_matches(db: Session = Depends(get_db)):
    return crud.get_all_matches(db)

@app.get("/api/matches/my", response_model=List[schemas.MatchResponse])
def get_my_matches(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return crud.get_matches_for_user(db, current_user.id)

@app.put("/api/matches/{match_id}/status", response_model=schemas.MatchResponse)
def update_match_status(
    match_id: int, 
    status_update: schemas.MatchStatusUpdate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    match = crud.get_match(db, match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
        
    # Security check: User must be owner of lost item or finder of found item
    lost_owner_id = match.lost_item.user_id
    found_reporter_id = match.found_item.reporter_id
    if current_user.id not in [lost_owner_id, found_reporter_id]:
        raise HTTPException(status_code=403, detail="Not authorized to update this match status")
        
    # Update match status
    updated_match = crud.update_match_status(db, match_id, status_update.status)
    
    # If the match was approved or claimed, we can update individual item statuses accordingly
    if status_update.status == "approved":
        match.lost_item.status = "matched"
        match.found_item.status = "matched"
    elif status_update.status == "resolved":
        match.lost_item.status = "claimed"
        match.found_item.status = "claimed"
    elif status_update.status == "rejected":
        match.lost_item.status = "pending"
        match.found_item.status = "pending"
        
    db.commit()
    return updated_match


# --- DEVELOPMENT UTILITIES ---

@app.get("/api/mock-emails", response_model=List[str])
def list_mock_emails():
    """Lists files in the mock email folder for debug viewing"""
    if not os.path.exists(MOCK_EMAIL_DIR):
        return []
    files = sorted([f for f in os.listdir(MOCK_EMAIL_DIR) if f.endswith(".html")], reverse=True)
    return files

@app.get("/api/mock-emails/{filename}", response_class=HTMLResponse)
def get_mock_email(filename: str):
    """Retrieves a specific mock email HTML body to view in frontend iframe"""
    filepath = os.path.join(MOCK_EMAIL_DIR, filename)
    # Path traversal protection
    real_path = os.path.abspath(filepath)
    real_mock_dir = os.path.abspath(MOCK_EMAIL_DIR)
    if not real_path.startswith(real_mock_dir):
        raise HTTPException(status_code=403, detail="Access denied")
        
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Email file not found")
        
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


# --- SERVE FILES & FRONTEND ---

# Route to serve uploads directory
app.mount("/backend/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Serve frontend static assets if they exist
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    
    # Fallback to serve index.html for any route not matched by backend APIs (to support routing)
    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str):
        index_file = os.path.join(static_dir, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"message": "Welcome to AI Lost & Found Assistant. Frontend static directory is empty."}
else:
    @app.get("/")
    def root():
        return {"message": "Welcome to AI Lost & Found Assistant Backend. Static folder not found."}
