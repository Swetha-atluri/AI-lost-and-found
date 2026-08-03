from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
from backend.app.database import User, LostItem, FoundItem, Match
from backend.app.schemas import UserCreate, LostItemCreate, FoundItemCreate
from backend.app.auth import get_password_hash

# --- User CRUD ---

def get_user(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, user: UserCreate) -> User:
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# --- Lost Item CRUD ---

def create_lost_item(db: Session, item: LostItemCreate, user_id: int, image_path: Optional[str] = None) -> LostItem:
    db_item = LostItem(
        user_id=user_id,
        name=item.name,
        category=item.category,
        description=item.description,
        date_lost=item.date_lost,
        location=item.location,
        image_path=image_path,
        status="pending"
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def get_lost_items(db: Session, skip: int = 0, limit: int = 100) -> List[LostItem]:
    return db.query(LostItem).order_by(LostItem.created_at.desc()).offset(skip).limit(limit).all()

def get_lost_item(db: Session, item_id: int) -> Optional[LostItem]:
    return db.query(LostItem).filter(LostItem.id == item_id).first()

def get_user_lost_items(db: Session, user_id: int) -> List[LostItem]:
    return db.query(LostItem).filter(LostItem.user_id == user_id).order_by(LostItem.created_at.desc()).all()


# --- Found Item CRUD ---

def create_found_item(db: Session, item: FoundItemCreate, reporter_id: int, image_path: Optional[str] = None) -> FoundItem:
    db_item = FoundItem(
        reporter_id=reporter_id,
        description=item.description,
        date_found=item.date_found,
        location=item.location,
        image_path=image_path,
        status="pending"
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def get_found_items(db: Session, skip: int = 0, limit: int = 100) -> List[FoundItem]:
    return db.query(FoundItem).order_by(FoundItem.created_at.desc()).offset(skip).limit(limit).all()

def get_found_item(db: Session, item_id: int) -> Optional[FoundItem]:
    return db.query(FoundItem).filter(FoundItem.id == item_id).first()

def get_user_found_items(db: Session, user_id: int) -> List[FoundItem]:
    return db.query(FoundItem).filter(FoundItem.reporter_id == user_id).order_by(FoundItem.created_at.desc()).all()


# --- Match CRUD ---

def create_match(db: Session, lost_item_id: int, found_item_id: int, confidence_score: float) -> Match:
    db_match = Match(
        lost_item_id=lost_item_id,
        found_item_id=found_item_id,
        confidence_score=confidence_score,
        status="pending"
    )
    db.add(db_match)
    db.commit()
    db.refresh(db_match)
    return db_match

def get_match(db: Session, match_id: int) -> Optional[Match]:
    return db.query(Match).filter(Match.id == match_id).first()

def get_all_matches(db: Session, skip: int = 0, limit: int = 100) -> List[Match]:
    return db.query(Match).order_by(Match.confidence_score.desc()).offset(skip).limit(limit).all()

def get_matches_for_user(db: Session, user_id: int) -> List[Match]:
    # Returns matches where the user is either the owner of the lost item or the reporter of the found item
    return db.query(Match).join(LostItem).filter(
        (LostItem.user_id == user_id) | (Match.found_item.has(reporter_id=user_id))
    ).order_by(Match.created_at.desc()).all()

def update_match_status(db: Session, match_id: int, status: str) -> Optional[Match]:
    db_match = get_match(db, match_id)
    if db_match:
        db_match.status = status
        db.commit()
        db.refresh(db_match)
    return db_match
