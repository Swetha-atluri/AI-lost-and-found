from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from backend.app.config import DATABASE_URL

# Create database engine
# connect_args={"check_same_thread": False} is needed for SQLite to run across threads
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# DB Session dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    lost_items = relationship("LostItem", back_populates="owner")
    found_items = relationship("FoundItem", back_populates="reporter")


class LostItem(Base):
    __tablename__ = "lost_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    date_lost = Column(DateTime, nullable=False)
    location = Column(String, nullable=False)
    image_path = Column(String, nullable=True)  # Store relative path e.g. "uploads/abc.jpg"
    status = Column(String, default="pending")  # pending, matched, claimed
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    owner = relationship("User", back_populates="lost_items")
    matches = relationship("Match", back_populates="lost_item")


class FoundItem(Base):
    __tablename__ = "found_items"

    id = Column(Integer, primary_key=True, index=True)
    reporter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    description = Column(Text, nullable=False)
    date_found = Column(DateTime, nullable=False)
    location = Column(String, nullable=False)
    image_path = Column(String, nullable=True)  # Store relative path
    status = Column(String, default="pending")  # pending, matched, claimed
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    reporter = relationship("User", back_populates="found_items")
    matches = relationship("Match", back_populates="found_item")


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    lost_item_id = Column(Integer, ForeignKey("lost_items.id"), nullable=False)
    found_item_id = Column(Integer, ForeignKey("found_items.id"), nullable=False)
    confidence_score = Column(Float, nullable=False)  # 0.0 to 1.0
    status = Column(String, default="pending")  # pending, approved, rejected, resolved
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    lost_item = relationship("LostItem", back_populates="matches")
    found_item = relationship("FoundItem", back_populates="matches")
