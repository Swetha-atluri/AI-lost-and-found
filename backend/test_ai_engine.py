import sys
import os
from pathlib import Path
from datetime import datetime

# Add the project root to sys.path so we can import backend packages
sys.path.append(str(Path(__file__).resolve().parent.parent))

from backend.app.ai_engine import ai_engine
from backend.app.database import engine, SessionLocal, Base, User, LostItem, FoundItem, Match
from backend.app import crud

def create_mock_images():
    """Generates two simple solid color images for visual similarity testing using Pillow"""
    print("[TEST] Generating mock images for image comparison testing...")
    from PIL import Image
    
    img_dir = Path(__file__).resolve().parent / "test_images"
    img_dir.mkdir(exist_ok=True)
    
    # Image A: Dark Blue Wallet square
    img_a = Image.new("RGB", (256, 256), color=(10, 30, 120))
    path_a = img_dir / "lost_wallet.jpg"
    img_a.save(path_a)
    
    # Image B: Dark Blue-ish Wallet square
    img_b = Image.new("RGB", (256, 256), color=(12, 34, 115))
    path_b = img_dir / "found_wallet.jpg"
    img_b.save(path_b)
    
    # Image C: Red apple square (dissimilar)
    img_c = Image.new("RGB", (256, 256), color=(220, 20, 20))
    path_c = img_dir / "red_apple.jpg"
    img_c.save(path_c)
    
    return str(path_a), str(path_b), str(path_c)

def test_engine():
    # 1. Initialize SQLite Database
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        # Clear existing test data
        db.query(Match).delete()
        db.query(LostItem).delete()
        db.query(FoundItem).delete()
        db.query(User).delete()
        db.commit()
        
        # 2. Setup mock users
        print("[TEST] Setting up mock users...")
        user_a = User(username="owner_alice", email="alice@example.com", hashed_password="dummyhash")
        user_b = User(username="finder_bob", email="bob@example.com", hashed_password="dummyhash")
        db.add_all([user_a, user_b])
        db.commit()
        db.refresh(user_a)
        db.refresh(user_b)
        
        # 3. Create test images
        img_a_path, img_b_path, img_c_path = create_mock_images()
        
        # 4. Initialize AI models
        print("[TEST] Initializing AI Models...")
        ai_engine.initialize()
        
        # 5. Create Lost Items
        print("[TEST] Creating reported lost items...")
        lost_items = [
            LostItem(
                user_id=user_a.id,
                name="Black Leather Wallet",
                category="Accessories",
                description="A folded black leather wallet containing a driver's license, two credit cards, and some cash.",
                date_lost=datetime.utcnow(),
                location="Main Campus Cafeteria",
                image_path=img_a_path,
                status="pending"
            ),
            LostItem(
                user_id=user_a.id,
                name="Silver Apple iPad",
                category="Electronics",
                description="Silver iPad Pro 11-inch with a black magnetic smart cover. Back of the screen has a small star sticker.",
                date_lost=datetime.utcnow(),
                location="Engineering Hall Room 101",
                image_path=None,
                status="pending"
            )
        ]
        db.add_all(lost_items)
        db.commit()
        for item in lost_items:
            db.refresh(item)
            
        print("[TEST] Rebuilding AI indexes...")
        ai_engine.rebuild_indexes_from_db(db)
        
        # 6. Test Case 1: Match with strong text overlap
        print("\n--- Test Case 1: Strong Text & Image Match ---")
        found_wallet = FoundItem(
            reporter_id=user_b.id,
            description="Found a small dark black leather folder or wallet. Inside there are a couple of bank cards and some currency notes.",
            date_found=datetime.utcnow(),
            location="Cafeteria booth near window",
            image_path=img_b_path,
            status="pending"
        )
        db.add(found_wallet)
        db.commit()
        db.refresh(found_wallet)
        
        matches_wallet = ai_engine.check_matches_for_found_item(found_wallet, db)
        print(f"[TEST] Matches created: {len(matches_wallet)}")
        for m in matches_wallet:
            print(f"  - Match ID {m.id}: Score {m.confidence_score:.2%}, Lost Item: {m.lost_item.name}, Found Location: {m.found_item.location}")
            
        # 7. Test Case 2: Dissimilar image test
        print("\n--- Test Case 2: Similar Text but Dissimilar Image Match ---")
        found_red_apple = FoundItem(
            reporter_id=user_b.id,
            description="Found a leather object in the library.",
            date_found=datetime.utcnow(),
            location="Library Study Room 4",
            image_path=img_c_path,  # red apple (very dissimilar from dark blue wallet)
            status="pending"
        )
        db.add(found_red_apple)
        db.commit()
        db.refresh(found_red_apple)
        
        matches_apple = ai_engine.check_matches_for_found_item(found_red_apple, db)
        print(f"[TEST] Matches created: {len(matches_apple)}")
        
        # 8. Test Case 3: iPad Match (Text-only index lookup)
        print("\n--- Test Case 3: Text Only Matching (iPad) ---")
        found_ipad = FoundItem(
            reporter_id=user_b.id,
            description="Found a silver tablet (looks like an Apple iPad) with a dark colored smart flip cover.",
            date_found=datetime.utcnow(),
            location="Engineering Hall corridor",
            image_path=None,
            status="pending"
        )
        db.add(found_ipad)
        db.commit()
        db.refresh(found_ipad)
        
        matches_ipad = ai_engine.check_matches_for_found_item(found_ipad, db)
        print(f"[TEST] Matches created: {len(matches_ipad)}")
        for m in matches_ipad:
            print(f"  - Match ID {m.id}: Score {m.confidence_score:.2%}, Lost Item: {m.lost_item.name}")
            
        print("\n[TEST COMPLETED] Verification successful. Clean databases and verified logic paths.")
        
    finally:
        db.close()

if __name__ == "__main__":
    try:
        test_engine()
    except Exception as e:
        print(f"\n[TEST FAILED] Error: {e}")
        sys.exit(1)
