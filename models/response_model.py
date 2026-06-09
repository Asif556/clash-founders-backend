"""
models/response_model.py
------------------------
Response data access layer.
Handles recording and querying participant answers/responses.
"""

import logging
from datetime import datetime, timezone
from bson import ObjectId
from database.mongodb import get_db

logger = logging.getLogger(__name__)


def record_response(
    participant_id: str,
    question_id: str,
    selected_option: str,
    response_time: float,
    points_awarded: int,
    is_correct: bool
) -> dict:
    """
    Record a participant's response to a question.
    
    Args:
        participant_id: The participant's ObjectId string
        question_id: The question's ObjectId string
        selected_option: The option text selected by the participant
        response_time: Time taken to answer in seconds
        points_awarded: Points awarded for this response
        is_correct: Whether the answer was correct
    
    Returns:
        The created response document
    
    Raises:
        ValueError: If participant already answered this question
    """
    db = get_db()

    # Check if participant already answered this question
    existing = db.responses.find_one({
        "participant_id": participant_id,
        "question_id": question_id
    })
    if existing:
        raise ValueError("Participant has already answered this question")

    response = {
        "participant_id": participant_id,
        "question_id": question_id,
        "selected_option": selected_option,
        "response_time": round(response_time, 3),
        "points_awarded": points_awarded,
        "is_correct": is_correct,
        "answered_at": datetime.now(timezone.utc)
    }

    result = db.responses.insert_one(response)
    response["_id"] = result.inserted_id
    logger.info(
        f"Response recorded: participant={participant_id}, "
        f"question={question_id}, correct={is_correct}, points={points_awarded}"
    )
    return response


def get_responses_for_question(question_id: str) -> list:
    """Get all responses for a specific question."""
    db = get_db()
    return list(db.responses.find({"question_id": question_id}))


def get_responses_for_participant(participant_id: str) -> list:
    """Get all responses from a specific participant."""
    db = get_db()
    return list(db.responses.find({"participant_id": participant_id}))


def has_answered(participant_id: str, question_id: str) -> bool:
    """Check if a participant has already answered a specific question."""
    db = get_db()
    return db.responses.find_one({
        "participant_id": participant_id,
        "question_id": question_id
    }) is not None


def delete_all_responses():
    """Delete all responses (for quiz reset)."""
    db = get_db()
    result = db.responses.delete_many({})
    logger.info(f"Deleted {result.deleted_count} responses")


def serialize_response(response: dict) -> dict:
    """Convert a response document to a JSON-safe dict."""
    if not response:
        return None
    return {
        "id": str(response["_id"]),
        "participant_id": response["participant_id"],
        "question_id": response["question_id"],
        "selected_option": response["selected_option"],
        "response_time": response["response_time"],
        "points_awarded": response["points_awarded"],
        "is_correct": response["is_correct"]
    }
