"""
routes/admin_routes.py
-----------------------
REST API routes for admin operations.
Handles quiz control endpoints: start, next, end, reset.
"""

import logging
from flask import Blueprint, jsonify, request
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
from models.question_model import get_question_count, get_all_questions, serialize_question, insert_questions, update_question, delete_question
from models.winner_model import save_winner, get_all_winners, delete_winner

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
    - Saves the #1 player to the winners collection
    
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

        # Save the top winner if there are participants
        if leaderboard and len(leaderboard) > 0:
            top_player = leaderboard[0]
            if top_player.get("score", 0) > 0:
                save_winner(
                    name=top_player.get("name"),
                    phone=top_player.get("phone"),
                    score=top_player.get("score")
                )
                logger.info(f"🏆 Saved winner: {top_player.get('name')}")

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


@admin_bp.route("/questions", methods=["POST"])
def add_question_route():
    """
    POST /api/admin/questions
    
    Add a new question to the database.
    """
    try:
        data = request.json
        if not data:
            return jsonify({"success": False, "message": "No data provided"}), 400
            
        question_text = data.get("question")
        options = data.get("options", [])
        correct_answer = data.get("correct_answer")
        
        if not question_text or len(options) < 2 or not correct_answer:
            return jsonify({"success": False, "message": "Missing or invalid required fields (question, options, correct_answer)"}), 400
            
        if correct_answer not in options:
            return jsonify({"success": False, "message": "Correct answer must be one of the options"}), 400
            
        new_question = {
            "question": question_text,
            "options": options,
            "correct_answer": correct_answer
        }
        
        insert_questions([new_question])
        
        logger.info(f"➕ Added new question: {question_text}")
        return jsonify({
            "success": True,
            "message": "Question added successfully!"
        }), 201

    except Exception as e:
        logger.error(f"Add question error: {e}")
        return jsonify({
            "success": False,
            "message": f"Failed to add question: {str(e)}"
        }), 500


@admin_bp.route("/questions/<question_id>", methods=["PUT"])
def edit_question_route(question_id):
    """
    PUT /api/admin/questions/<question_id>
    Update an existing question in the database.
    """
    try:
        data = request.json
        if not data:
            return jsonify({"success": False, "message": "No data provided"}), 400
            
        question_text = data.get("question")
        options = data.get("options", [])
        correct_answer = data.get("correct_answer")
        
        if not question_text or len(options) < 2 or not correct_answer:
            return jsonify({"success": False, "message": "Missing or invalid required fields"}), 400
            
        if correct_answer not in options:
            return jsonify({"success": False, "message": "Correct answer must be one of the options"}), 400
            
        updated_data = {
            "question": question_text,
            "options": options,
            "correct_answer": correct_answer
        }
        
        success = update_question(question_id, updated_data)
        if success:
            logger.info(f"✏️ Updated question: {question_id}")
            return jsonify({"success": True, "message": "Question updated successfully!"}), 200
        else:
            return jsonify({"success": False, "message": "Question not found or no changes made"}), 404

    except Exception as e:
        logger.error(f"Edit question error: {e}")
        return jsonify({"success": False, "message": f"Failed to update question: {str(e)}"}), 500


@admin_bp.route("/questions/<question_id>", methods=["DELETE"])
def delete_question_route(question_id):
    """
    DELETE /api/admin/questions/<question_id>
    Delete an existing question from the database.
    """
    try:
        success = delete_question(question_id)
        if success:
            logger.info(f"🗑️ Deleted question: {question_id}")
            return jsonify({"success": True, "message": "Question deleted successfully!"}), 200
        else:
            return jsonify({"success": False, "message": "Question not found"}), 404

    except Exception as e:
        logger.error(f"Delete question error: {e}")
        return jsonify({"success": False, "message": f"Failed to delete question: {str(e)}"}), 500


@admin_bp.route("/winners/<winner_id>", methods=["DELETE"])
def delete_winner_route(winner_id):
    """
    DELETE /api/admin/winners/<winner_id>
    Delete an existing winner from the database.
    """
    try:
        success = delete_winner(winner_id)
        if success:
            logger.info(f"🗑️ Deleted winner: {winner_id}")
            return jsonify({"success": True, "message": "Winner deleted successfully!"}), 200
        else:
            return jsonify({"success": False, "message": "Winner not found"}), 404

    except Exception as e:
        logger.error(f"Delete winner error: {e}")
        return jsonify({"success": False, "message": f"Failed to delete winner: {str(e)}"}), 500


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
            "questions": [...],
            "winners": [...]
        }
    """
    try:
        state = get_quiz_state()
        participants = get_all_participants()
        leaderboard = get_leaderboard()
        questions = get_all_questions()
        winners = get_all_winners()

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
            "questions": [serialize_question(q, include_answer=True) for q in questions],
            "winners": winners
        }), 200

    except Exception as e:
        logger.error(f"Admin status error: {e}")
        return jsonify({
            "success": False,
            "message": f"Failed to fetch admin status: {str(e)}"
        }), 500
