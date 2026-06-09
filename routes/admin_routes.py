"""
routes/admin_routes.py
-----------------------
REST API routes for admin operations.
Handles quiz control endpoints: start, next, end, reset.
"""

import logging
from flask import Blueprint, jsonify
from services.quiz_service import (
    start_quiz,
    end_quiz,
    reset_quiz,
    advance_to_next_question,
    get_quiz_state,
    get_current_question_with_options,
)
from models.participant_model import (
    get_leaderboard,
    get_all_participants,
    serialize_participant,
    delete_all_participants,
)
from models.response_model import delete_all_responses
from models.question_model import get_question_count, get_all_questions, serialize_question

logger = logging.getLogger(__name__)

# Create blueprint for admin routes
admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


@admin_bp.route("/start", methods=["POST"])
def start_quiz_route():
    """
    POST /api/admin/start
    
    Start the quiz.
    - Sets allow_join to false
    - Sets status to 'running'
    
    Response:
        { "success": true, "message": "Quiz started" }
    """
    try:
        state = get_quiz_state()
        if state["status"] == "running":
            return jsonify({
                "success": False,
                "message": "Quiz is already running"
            }), 400

        participants = get_all_participants()
        if len(participants) == 0:
            return jsonify({
                "success": False,
                "message": "Cannot start quiz with no participants"
            }), 400

        start_quiz()

        logger.info("🚀 Quiz started via REST API")
        return jsonify({
            "success": True,
            "message": "Quiz started! No new participants can join."
        }), 200

    except Exception as e:
        logger.error(f"Start quiz error: {e}")
        return jsonify({
            "success": False,
            "message": f"Failed to start quiz: {str(e)}"
        }), 500


@admin_bp.route("/next-question", methods=["POST"])
def next_question_route():
    """
    POST /api/admin/next-question
    
    Advance to the next question.
    
    Response:
        { "success": true, "message": "Advanced to next question" }
    """
    try:
        state = get_quiz_state()
        if state["status"] != "running":
            return jsonify({
                "success": False,
                "message": "Quiz is not running"
            }), 400

        result = advance_to_next_question()

        if result["has_next"]:
            return jsonify({
                "success": True,
                "message": f"Advanced to question {result['question_index'] + 1}",
                "question_index": result["question_index"]
            }), 200
        else:
            end_quiz()
            return jsonify({
                "success": True,
                "message": "No more questions. Quiz completed!",
                "quiz_completed": True
            }), 200

    except Exception as e:
        logger.error(f"Next question error: {e}")
        return jsonify({
            "success": False,
            "message": f"Failed to advance: {str(e)}"
        }), 500


@admin_bp.route("/end", methods=["POST"])
def end_quiz_route():
    """
    POST /api/admin/end
    
    End the quiz.
    - Sets status to 'completed'
    
    Response:
        {
            "success": true,
            "message": "Quiz ended",
            "leaderboard": [...]
        }
    """
    try:
        end_quiz()
        leaderboard = get_leaderboard()

        logger.info("🏁 Quiz ended via REST API")
        return jsonify({
            "success": True,
            "message": "Quiz ended. Final results are ready.",
            "leaderboard": leaderboard
        }), 200

    except Exception as e:
        logger.error(f"End quiz error: {e}")
        return jsonify({
            "success": False,
            "message": f"Failed to end quiz: {str(e)}"
        }), 500


@admin_bp.route("/reset", methods=["POST"])
def reset_quiz_route():
    """
    POST /api/admin/reset
    
    Reset the entire quiz.
    - Reset scores
    - Clear responses
    - Allow joining again
    
    Response:
        { "success": true, "message": "Quiz reset" }
    """
    try:
        reset_quiz()
        delete_all_participants()

        logger.info("🔄 Quiz fully reset via REST API")
        return jsonify({
            "success": True,
            "message": "Quiz has been completely reset. Participants can join again."
        }), 200

    except Exception as e:
        logger.error(f"Reset quiz error: {e}")
        return jsonify({
            "success": False,
            "message": f"Failed to reset quiz: {str(e)}"
        }), 500


@admin_bp.route("/status", methods=["GET"])
def get_admin_status():
    """
    GET /api/admin/status
    
    Get complete admin dashboard data.
    
    Response:
        {
            "success": true,
            "state": { ... },
            "participants": [...],
            "leaderboard": [...],
            "questions": [...]
        }
    """
    try:
        state = get_quiz_state()
        participants = get_all_participants()
        leaderboard = get_leaderboard()
        questions = get_all_questions()

        return jsonify({
            "success": True,
            "state": {
                "status": state.get("status", "waiting"),
                "current_question_index": state.get("current_question_index", 0),
                "allow_join": state.get("allow_join", True),
                "total_questions": len(questions),
                "participant_count": len(participants)
            },
            "participants": [serialize_participant(p) for p in participants],
            "leaderboard": leaderboard,
            "questions": [serialize_question(q, include_answer=True) for q in questions]
        }), 200

    except Exception as e:
        logger.error(f"Admin status error: {e}")
        return jsonify({
            "success": False,
            "message": f"Failed to fetch admin status: {str(e)}"
        }), 500
