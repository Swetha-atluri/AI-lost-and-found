import logging
import os
import cv2
import faiss
import numpy as np
from PIL import Image
from typing import List, Tuple, Dict, Optional
from sqlalchemy.orm import Session

from sentence_transformers import SentenceTransformer
from transformers import CLIPProcessor, CLIPModel

from backend.app.config import MATCH_THRESHOLD, TEXT_WEIGHT, IMAGE_WEIGHT
from backend.app.database import LostItem, FoundItem, Match
from backend.app import crud
from backend.app.email_service import send_match_notification

logger = logging.getLogger("ai_engine")

class AIEngine:
    def __init__(self):
        self.text_model = None
        self.clip_model = None
        self.clip_processor = None
        
        # FAISS indexes and mapping tables
        # Text dimensions = 384 (all-MiniLM-L6-v2)
        # Image dimensions = 512 (openai/clip-vit-base-patch32)
        self.text_index = None
        self.text_ids = []  # Maps FAISS index row to LostItem.id
        
        self.image_index = None
        self.image_ids = [] # Maps FAISS index row to LostItem.id
        
        self._initialized = False

    def initialize(self):
        """Lazy load the AI models and rebuild FAISS index from DB"""
        if self._initialized:
            return
            
        logger.info("Initializing AI models (this may take a minute on first run)...")
        print("[AI ENGINE] Loading models. This might take a moment if downloading for the first time...")
        
        # Load models
        try:
            self.text_model = SentenceTransformer("all-MiniLM-L6-v2")
            self.clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
            self.clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
            
            # Setup FAISS indexes (Inner Product is used for Cosine Similarity when vectors are normalized)
            self.text_index = faiss.IndexFlatIP(384)
            self.image_index = faiss.IndexFlatIP(512)
            
            self._initialized = True
            logger.info("AI Models loaded successfully.")
            print("[AI ENGINE] Models and FAISS indexes initialized successfully.")
        except Exception as e:
            logger.error(f"Error initializing models: {str(e)}")
            print(f"[AI ENGINE ERROR] Failed to load models: {str(e)}")
            raise e

    def preprocess_image_opencv(self, image_path: str) -> Optional[Image.Image]:
        """Loads and preprocesses image using OpenCV and returns a PIL Image for CLIP"""
        if not image_path or not os.path.exists(image_path):
            return None
        try:
            # Load image using OpenCV
            img = cv2.imread(image_path)
            if img is None:
                return None
            
            # Convert BGR (OpenCV default) to RGB
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # Let's perform basic preprocessing (e.g., resizing while maintaining aspect ratio, or simple denoising)
            # Denoising can improve visual similarity matching
            img_filtered = cv2.fastNlMeansDenoisingColored(img_rgb, None, 10, 10, 7, 21)
            
            # Convert back to PIL Image for CLIP compatibility
            return Image.fromarray(img_filtered)
        except Exception as e:
            logger.error(f"Error preprocessing image {image_path}: {e}")
            # Fallback to standard PIL loading if OpenCV fails
            try:
                return Image.open(image_path).convert("RGB")
            except Exception:
                return None

    def get_text_embedding(self, text: str) -> np.ndarray:
        self.initialize()
        embedding = self.text_model.encode([text])[0]
        # Normalize vector for cosine similarity
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        return embedding

    def get_image_embedding(self, image_path: str) -> Optional[np.ndarray]:
        self.initialize()
        pil_img = self.preprocess_image_opencv(image_path)
        if pil_img is None:
            return None
            
        try:
            inputs = self.clip_processor(images=pil_img, return_tensors="pt")
            import torch
            with torch.no_grad():
                image_features = self.clip_model.get_image_features(**inputs)
            
            # Convert to numpy
            embedding = image_features.numpy()[0]
            # Normalize vector
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
            return embedding
        except Exception as e:
            logger.error(f"CLIP encoding failed for {image_path}: {e}")
            return None

    def rebuild_indexes_from_db(self, db: Session):
        """Rebuilds text and image FAISS indexes from all active lost items in the database"""
        self.initialize()
        
        # Reset FAISS indexes
        self.text_index.reset()
        self.text_ids = []
        
        self.image_index.reset()
        self.image_ids = []
        
        # Fetch active lost items
        lost_items = db.query(LostItem).filter(LostItem.status == "pending").all()
        
        text_embeddings = []
        image_embeddings = []
        
        for item in lost_items:
            # 1. Text embedding
            text_str = f"{item.name} {item.category} {item.description}"
            text_emb = self.get_text_embedding(text_str)
            text_embeddings.append(text_emb)
            self.text_ids.append(item.id)
            
            # 2. Image embedding (if image exists)
            if item.image_path:
                img_emb = self.get_image_embedding(item.image_path)
                if img_emb is not None:
                    image_embeddings.append(img_emb)
                    self.image_ids.append(item.id)
                    
        # Add to FAISS index if lists are not empty
        if text_embeddings:
            text_matrix = np.array(text_embeddings).astype('float32')
            self.text_index.add(text_matrix)
            logger.info(f"Added {len(text_embeddings)} items to FAISS text index.")
            
        if image_embeddings:
            image_matrix = np.array(image_embeddings).astype('float32')
            self.image_index.add(image_matrix)
            logger.info(f"Added {len(image_embeddings)} items to FAISS image index.")

    def add_lost_item(self, item: LostItem):
        """Adds a newly created LostItem to the FAISS indexes dynamically"""
        self.initialize()
        
        # 1. Text index addition
        text_str = f"{item.name} {item.category} {item.description}"
        text_emb = self.get_text_embedding(text_str)
        
        text_matrix = np.expand_dims(text_emb, axis=0).astype('float32')
        self.text_index.add(text_matrix)
        self.text_ids.append(item.id)
        
        # 2. Image index addition (if image exists)
        if item.image_path:
            img_emb = self.get_image_embedding(item.image_path)
            if img_emb is not None:
                image_matrix = np.expand_dims(img_emb, axis=0).astype('float32')
                self.image_index.add(image_matrix)
                self.image_ids.append(item.id)
                logger.info(f"Dynamically added LostItem {item.id} to text and image FAISS indexes.")
            else:
                logger.info(f"Dynamically added LostItem {item.id} to text FAISS index only (image embed failed).")
        else:
            logger.info(f"Dynamically added LostItem {item.id} to text FAISS index only.")

    def check_matches_for_found_item(self, found_item: FoundItem, db: Session) -> List[Match]:
        """
        Calculates similarity scores between a new FoundItem and all pending LostItems.
        Creates matches for any item exceeding config.MATCH_THRESHOLD.
        Sends email notifications when a match is successfully registered.
        """
        self.initialize()
        
        # Rebuild/validate indexes first to make sure everything is in sync
        # Since this is a demo, rebuilding on match query is safe and keeps things perfectly consistent
        self.rebuild_indexes_from_db(db)
        
        if len(self.text_ids) == 0:
            logger.info("No active lost items to compare against.")
            return []
            
        # Get embeddings for the found item
        found_text_str = found_item.description
        found_text_emb = self.get_text_embedding(found_text_str)
        
        found_img_emb = None
        if found_item.image_path:
            found_img_emb = self.get_image_embedding(found_item.image_path)
            
        # We will compute matching scores manually using the embeddings to combine text + image similarities
        matches_found = []
        
        # Fetch all pending lost items
        lost_items = db.query(LostItem).filter(LostItem.status == "pending").all()
        
        for lost in lost_items:
            # 1. Compute text similarity (cosine similarity)
            lost_text_str = f"{lost.name} {lost.category} {lost.description}"
            lost_text_emb = self.get_text_embedding(lost_text_str)
            text_sim = float(np.dot(found_text_emb, lost_text_emb))
            
            # 2. Compute image similarity if BOTH have images
            image_sim = None
            if found_img_emb is not None and lost.image_path:
                lost_img_emb = self.get_image_embedding(lost.image_path)
                if lost_img_emb is not None:
                    image_sim = float(np.dot(found_img_emb, lost_img_emb))
            
            # 3. Calculate final confidence score
            if image_sim is not None:
                # Weighted average of text and image similarity
                confidence = (TEXT_WEIGHT * text_sim) + (IMAGE_WEIGHT * image_sim)
                logger.info(f"Match Lost {lost.id} vs Found {found_item.id}: Text {text_sim:.3f}, Image {image_sim:.3f}, Combined {confidence:.3f}")
            else:
                # Text similarity only
                confidence = text_sim
                logger.info(f"Match Lost {lost.id} vs Found {found_item.id}: Text {text_sim:.3f} (No image overlap), Combined {confidence:.3f}")
                
            # If confidence exceeds matching threshold, we trigger a match
            if confidence >= MATCH_THRESHOLD:
                # Check if this match already exists to avoid duplicates
                existing_match = db.query(Match).filter(
                    Match.lost_item_id == lost.id,
                    Match.found_item_id == found_item.id
                ).first()
                
                if not existing_match:
                    # Create the match record
                    db_match = crud.create_match(db, lost.id, found_item.id, confidence)
                    
                    # Update statuses to matched
                    lost.status = "matched"
                    found_item.status = "matched"
                    db.commit()
                    
                    # Send email alert to lost item owner
                    send_match_notification(db_match, db)
                    
                    matches_found.append(db_match)
                    print(f"[MATCH FOUND] Match ID: {db_match.id} (Score: {confidence:.2%}) created between Lost: {lost.name} and Found!")
                    
        return matches_found

# Instantiate a global instance of AIEngine
ai_engine = AIEngine()
