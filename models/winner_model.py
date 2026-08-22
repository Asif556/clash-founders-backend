"""
models/winner_model.py
----------------------
Handles CRUD operations for the winners collection in MongoDB.
"""

import logging
from datetime import datetime
from bson import ObjectId
from database.mongodb import get_db

logger = logging.getLogger(__name__)


def save_winner(name: str, phone: str, score: int) -> str:
    """Save a quiz winner to the database."""
    try:
        db = get_db()
        winner = {
            "name": name,
            "phone": phone,
            "score": score,
            "date": datetime.utcnow().isoformat() + "Z"
        }
        result = db.winners.insert_one(winner)
        return str(result.inserted_id)
    except Exception as e:
        logger.error(f"Error saving winner: {e}")
        return None


def get_all_winners() -> list:
    """Fetch all winners from the database."""
    try:
        db = get_db()
        winners = list(db.winners.find().sort("date", -1))
        
        # Serialize ObjectIds to strings
        for winner in winners:
            winner["id"] = str(winner["_id"])
            del winner["_id"]
            
        return winners
    except Exception as e:
        logger.error(f"Error fetching winners: {e}")
        return []


def delete_winner(winner_id: str) -> bool:
    """Delete a specific winner by their ID."""
    try:
        db = get_db()
        result = db.winners.delete_one({"_id": ObjectId(winner_id)})
        return result.deleted_count > 0
    except Exception as e:
        logger.error(f"Error deleting winner {winner_id}: {e}")
        return False
