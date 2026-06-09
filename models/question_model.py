"""
models/question_model.py
------------------------
Question data access layer.
Handles CRUD operations for the questions collection.
"""

import logging
from bson import ObjectId
from database.mongodb import get_db

logger = logging.getLogger(__name__)


def get_all_questions() -> list:
    """Fetch all questions from the database, ordered by their insertion order."""
    db = get_db()
    return list(db.questions.find())


def get_question_by_index(index: int) -> dict:
    """
    Get a question by its position index (0-based).
    Questions are returned in insertion order.
    """
    db = get_db()
    questions = list(db.questions.find().skip(index).limit(1))
    return questions[0] if questions else None


def get_question_by_id(question_id: str) -> dict:
    """Fetch a question by its ObjectId."""
    db = get_db()
    return db.questions.find_one({"_id": ObjectId(question_id)})


def get_question_count() -> int:
    """Get total number of questions in the database."""
    db = get_db()
    return db.questions.count_documents({})


def insert_questions(questions: list) -> int:
    """
    Insert multiple questions into the database.
    
    Args:
        questions: List of question dicts with 'question', 'options', 'correct_answer'
    
    Returns:
        Number of questions inserted
    """
    db = get_db()
    if not questions:
        return 0
    result = db.questions.insert_many(questions)
    count = len(result.inserted_ids)
    logger.info(f"✅ Inserted {count} questions")
    return count


def delete_all_questions():
    """Delete all questions from the database."""
    db = get_db()
    result = db.questions.delete_many({})
    logger.info(f"Deleted {result.deleted_count} questions")


def serialize_question(question: dict, include_answer: bool = False) -> dict:
    """
    Convert a question document to a JSON-safe dict.
    
    Args:
        question: The question document from MongoDB
        include_answer: Whether to include the correct_answer field
    
    Returns:
        JSON-safe question dict
    """
    if not question:
        return None

    result = {
        "id": str(question["_id"]),
        "question": question["question"],
        "options": question["options"],
    }

    if include_answer:
        result["correct_answer"] = question["correct_answer"]

    return result


def serialize_question_without_options(question: dict) -> dict:
    """
    Serialize a question WITHOUT options (for Phase 1 - intro).
    Only sends the question text.
    """
    if not question:
        return None

    return {
        "id": str(question["_id"]),
        "question": question["question"],
    }
