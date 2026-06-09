"""
services/quiz_service.py
------------------------
Core quiz game logic service.
Manages quiz state, question flow, and coordinates between
participants, questions, responses, and scoring.
"""

import logging
from database.mongodb import get_db
from models.participant_model import (
    get_leaderboard,
    update_score,
    add_answer,
    reset_all_participants,
    delete_all_participants,
)
from models.question_model import (
    get_all_questions,
    get_question_by_index,
    get_question_count,
    serialize_question,
    serialize_question_without_options,
)
from models.response_model import (
    record_response,
    has_answered,
    delete_all_responses,
)
from services.scoring_service import calculate_points

logger = logging.getLogger(__name__)


# ── Quiz State Management ──────────────────────────────────────────

def get_quiz_state() -> dict:
    """Get the current quiz state from the database."""
    db = get_db()
    state = db.quiz_state.find_one({"_id": "quiz_state"})
    if not state:
        # Initialize default state
        state = {
            "_id": "quiz_state",
            "status": "waiting",
            "current_question_index": 0,
            "allow_join": True
        }
        db.quiz_state.insert_one(state)
    return state


def update_quiz_state(updates: dict):
    """Update the quiz state document with the given fields."""
    db = get_db()
    db.quiz_state.update_one(
        {"_id": "quiz_state"},
        {"$set": updates}
    )
    logger.info(f"Quiz state updated: {updates}")


def start_quiz():
    """
    Start the quiz.
    - Blocks new participants from joining
    - Sets status to 'running'
    - Resets question index to 0
    """
    update_quiz_state({
        "status": "running",
        "current_question_index": 0,
        "allow_join": False
    })
    logger.info("🚀 Quiz started!")


def end_quiz():
    """
    End the quiz.
    - Sets status to 'completed'
    """
    update_quiz_state({
        "status": "completed",
        "allow_join": False
    })
    logger.info("🏁 Quiz ended!")


def reset_quiz():
    """
    Reset the entire quiz.
    - Reset quiz state to waiting
    - Clear all responses
    - Reset all participant scores
    - Allow new joins
    """
    update_quiz_state({
        "status": "waiting",
        "current_question_index": 0,
        "allow_join": True
    })
    reset_all_participants()
    delete_all_responses()
    logger.info("🔄 Quiz has been fully reset")


def advance_to_next_question() -> dict:
    """
    Move to the next question.
    
    Returns:
        dict with 'has_next' bool and 'question_index' int
    """
    state = get_quiz_state()
    next_index = state["current_question_index"] + 1
    total = get_question_count()

    if next_index >= total:
        logger.info("No more questions remaining")
        return {"has_next": False, "question_index": next_index}

    update_quiz_state({"current_question_index": next_index})
    logger.info(f"Advanced to question {next_index + 1}/{total}")
    return {"has_next": True, "question_index": next_index}


# ── Question Retrieval ──────────────────────────────────────────

def get_current_question_intro() -> dict:
    """
    Get the current question for Phase 1 (intro).
    Returns question text WITHOUT options.
    """
    state = get_quiz_state()
    question = get_question_by_index(state["current_question_index"])
    if not question:
        return None

    data = serialize_question_without_options(question)
    data["question_number"] = state["current_question_index"] + 1
    data["total_questions"] = get_question_count()
    return data


def get_current_question_with_options() -> dict:
    """
    Get the current question for Phase 2 (answering).
    Returns question text WITH options but WITHOUT correct answer.
    """
    state = get_quiz_state()
    question = get_question_by_index(state["current_question_index"])
    if not question:
        return None

    data = serialize_question(question, include_answer=False)
    data["question_number"] = state["current_question_index"] + 1
    data["total_questions"] = get_question_count()
    return data


def get_current_question_correct_answer() -> dict:
    """
    Get the correct answer for the current question (Phase 3 - reveal).
    """
    state = get_quiz_state()
    question = get_question_by_index(state["current_question_index"])
    if not question:
        return None

    return {
        "id": str(question["_id"]),
        "question": question["question"],
        "options": question["options"],
        "correct_answer": question["correct_answer"],
        "question_number": state["current_question_index"] + 1,
        "total_questions": get_question_count()
    }


# ── Answer Processing ──────────────────────────────────────────

def process_answer(participant_id: str, selected_option: str, response_time_ms: float) -> dict:
    """
    Process a participant's answer submission.
    
    Args:
        participant_id: The participant's ID
        selected_option: The option text selected
        response_time_ms: Time taken in milliseconds
    
    Returns:
        Result dict with is_correct, points, and message
    
    Raises:
        ValueError: If answer is invalid (duplicate, quiz not running, etc.)
    """
    state = get_quiz_state()

    # Validate quiz is running
    if state["status"] != "running":
        raise ValueError("Quiz is not currently running")

    # Get current question
    question = get_question_by_index(state["current_question_index"])
    if not question:
        raise ValueError("No active question")

    question_id = str(question["_id"])

    # Check for duplicate answer
    if has_answered(participant_id, question_id):
        raise ValueError("You have already answered this question")

    # Validate response time (must be within 10 seconds)
    response_time_seconds = response_time_ms / 1000
    if response_time_seconds > 15:  # Allow small buffer over 10s
        raise ValueError("Answer submitted after timer expired")

    # Determine correctness
    is_correct = selected_option == question["correct_answer"]

    # Calculate points
    points = calculate_points(response_time_seconds, is_correct)

    # Record the response in the responses collection
    record_response(
        participant_id=participant_id,
        question_id=question_id,
        selected_option=selected_option,
        response_time=response_time_seconds,
        points_awarded=points,
        is_correct=is_correct
    )

    # Update participant's total score
    if points > 0:
        update_score(participant_id, points)

    # Add answer to participant's answers array
    answer_record = {
        "questionId": question_id,
        "selected": selected_option,
        "timeMs": response_time_ms,
        "correct": is_correct,
        "points": points
    }
    add_answer(participant_id, answer_record)

    logger.info(
        f"Answer processed: participant={participant_id}, "
        f"correct={is_correct}, points={points}, time={response_time_seconds:.2f}s"
    )

    return {
        "is_correct": is_correct,
        "points": points,
        "response_time": response_time_seconds,
        "message": f"+{points} points!" if is_correct else "Wrong answer!"
    }
