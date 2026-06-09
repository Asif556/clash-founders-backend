"""
socketio_events/quiz_events.py
-------------------------------
Socket.IO event handlers for real-time quiz interactions.
Manages WebSocket events for the quiz flow including:
- Participant joining the lobby
- Admin quiz controls (start, next, end)
- Answer submission
- Phase transitions with server-side timers
"""

import logging
from flask_socketio import emit, join_room, leave_room
from flask import request

from services.quiz_service import (
    get_quiz_state,
    start_quiz,
    end_quiz,
    reset_quiz,
    advance_to_next_question,
    get_current_question_intro,
    get_current_question_with_options,
    get_current_question_correct_answer,
    process_answer,
)
from models.participant_model import (
    get_participant_by_id,
    get_participant_by_socket,
    update_socket_id,
    get_leaderboard,
    serialize_participant,
)
from models.question_model import get_question_count
from utils.timer_utils import schedule_phase_transition, cancel_all_timers
from config import Config

logger = logging.getLogger(__name__)

# Room names
QUIZ_ROOM = "quiz_room"
ADMIN_ROOM = "admin_room"


def register_socketio_events(socketio):
    """Register all Socket.IO event handlers on the given socketio instance."""

    @socketio.on("connect")
    def handle_connect():
        """Handle new WebSocket connection."""
        sid = request.sid
        logger.info(f"🔌 Client connected: {sid}")
        print("Client Connected")
        emit("connection_ack", {"message": "Connected to quiz server", "sid": sid})

    @socketio.on("disconnect")
    def handle_disconnect():
        """Handle WebSocket disconnection."""
        sid = request.sid
        logger.info(f"🔌 Client disconnected: {sid}")

    # ── Lobby Events ────────────────────────────────────────────

    @socketio.on("join_lobby")
    def handle_join_lobby(data):
        """
        Participant joins the quiz lobby room.
        
        Expected data:
            { "participant_id": "..." }
        """
        sid = request.sid
        participant_id = data.get("participant_id")

        if not participant_id:
            emit("error", {"message": "participant_id is required"})
            return

        # Update participant's socket ID
        update_socket_id(participant_id, sid)

        # Join the quiz room
        join_room(QUIZ_ROOM)

        participant = get_participant_by_id(participant_id)
        if participant:
            serialized = serialize_participant(participant)
            logger.info(f"👤 {serialized['name']} joined the lobby (sid: {sid})")

            # Notify all clients in the room about the new participant
            emit("participant_joined", serialized, room=QUIZ_ROOM)

            # Send current quiz state to the joining participant
            state = get_quiz_state()
            emit("quiz_state_update", {
                "status": state["status"],
                "current_question_index": state["current_question_index"],
                "allow_join": state["allow_join"],
                "total_questions": get_question_count()
            })

            # Send current leaderboard
            leaderboard = get_leaderboard()
            emit("leaderboard_update", {"leaderboard": leaderboard}, room=QUIZ_ROOM)
        else:
            emit("error", {"message": "Participant not found"})

    # ── Admin Events ────────────────────────────────────────────

    @socketio.on("admin_join")
    def handle_admin_join():
        """Admin joins the admin room for admin-specific events."""
        sid = request.sid
        join_room(ADMIN_ROOM)
        join_room(QUIZ_ROOM)
        logger.info(f"🛡️ Admin connected: {sid}")
        emit("admin_ack", {"message": "Admin connected"})

    @socketio.on("admin_start_quiz")
    def handle_admin_start_quiz():
        """
        Admin starts the quiz.
        - Blocks new joins
        - Sets status to 'running'
        - Broadcasts quiz_started to all participants
        - Sends first question (intro phase)
        """
        logger.info("🚀 Admin triggered quiz start")
        start_quiz()

        # Notify all participants that the quiz has started
        emit("quiz_started", {
            "message": "The quiz has begun!",
            "total_questions": get_question_count()
        }, room=QUIZ_ROOM)

        # Start the first question automatically
        _start_question_phase(socketio)

    @socketio.on("admin_next_question")
    def handle_admin_next_question():
        """
        Admin advances to the next question.
        Cancels any active timers and starts the next question flow.
        """
        logger.info("⏭️ Admin triggered next question")
        cancel_all_timers()

        result = advance_to_next_question()

        if result["has_next"]:
            _start_question_phase(socketio)
        else:
            # No more questions — end the quiz
            _finish_quiz(socketio)

    @socketio.on("admin_end_quiz")
    def handle_admin_end_quiz():
        """Admin ends the quiz immediately."""
        logger.info("🛑 Admin triggered quiz end")
        cancel_all_timers()
        _finish_quiz(socketio)

    # ── Answer Submission ────────────────────────────────────────

    @socketio.on("submit_answer")
    def handle_submit_answer(data):
        """
        Participant submits an answer.
        
        Expected data:
            {
                "participant_id": "...",
                "selected_option": "...",
                "response_time_ms": 1234
            }
        """
        sid = request.sid
        participant_id = data.get("participant_id")
        selected_option = data.get("selected_option")
        response_time_ms = data.get("response_time_ms", 0)

        if not all([participant_id, selected_option is not None]):
            emit("error", {"message": "Missing required fields"})
            return

        try:
            result = process_answer(
                participant_id=participant_id,
                selected_option=selected_option,
                response_time_ms=float(response_time_ms)
            )

            # Send result back to the submitting participant
            emit("answer_submitted", {
                "success": True,
                "is_correct": result["is_correct"],
                "points": result["points"],
                "message": result["message"]
            })

            logger.info(
                f"✅ Answer from {participant_id}: "
                f"correct={result['is_correct']}, points={result['points']}"
            )

        except ValueError as e:
            emit("answer_submitted", {
                "success": False,
                "message": str(e)
            })
            logger.warning(f"Answer rejected: {e}")

        except Exception as e:
            emit("error", {"message": f"Server error: {str(e)}"})
            logger.error(f"Answer processing error: {e}")


def _start_question_phase(socketio):
    """
    Phase 1: Show question text only (intro phase).
    After QUESTION_INTRO_DURATION seconds, transition to Phase 2.
    """
    question_data = get_current_question_intro()
    if not question_data:
        logger.warning("No question found for intro phase")
        _finish_quiz(socketio)
        return

    logger.info(
        f"📖 Phase 1 (Intro): Question {question_data['question_number']}"
        f"/{question_data['total_questions']}"
    )

    # Broadcast question without options to all participants
    socketio.emit("show_question", {
        "phase": "intro",
        "question": question_data["question"],
        "question_number": question_data["question_number"],
        "total_questions": question_data["total_questions"],
        "question_id": question_data["id"],
        "duration": Config.QUESTION_INTRO_DURATION
    }, room=QUIZ_ROOM)

    # Schedule transition to Phase 2 after intro duration
    schedule_phase_transition(
        "intro_to_answering",
        Config.QUESTION_INTRO_DURATION,
        _start_answering_phase,
        socketio
    )


def _start_answering_phase(socketio):
    """
    Phase 2: Show options and accept answers.
    After ANSWER_DURATION seconds, transition to Phase 3.
    """
    question_data = get_current_question_with_options()
    if not question_data:
        logger.warning("No question found for answering phase")
        return

    logger.info(
        f"🎯 Phase 2 (Answering): Question {question_data['question_number']}"
        f"/{question_data['total_questions']}"
    )

    # Broadcast question WITH options
    socketio.emit("show_options", {
        "phase": "answering",
        "question": question_data["question"],
        "options": question_data["options"],
        "question_number": question_data["question_number"],
        "total_questions": question_data["total_questions"],
        "question_id": question_data["id"],
        "duration": Config.ANSWER_DURATION
    }, room=QUIZ_ROOM)

    # Schedule transition to reveal phase
    schedule_phase_transition(
        "answering_to_reveal",
        Config.ANSWER_DURATION,
        _start_reveal_phase,
        socketio
    )


def _start_reveal_phase(socketio):
    """
    Phase 3: Reveal the correct answer and update leaderboard.
    """
    answer_data = get_current_question_correct_answer()
    if not answer_data:
        logger.warning("No question found for reveal phase")
        return

    logger.info(
        f"✅ Phase 3 (Reveal): Question {answer_data['question_number']}"
        f"/{answer_data['total_questions']}"
    )

    # Broadcast correct answer
    socketio.emit("show_correct_answer", {
        "phase": "reveal",
        "question": answer_data["question"],
        "options": answer_data["options"],
        "correct_answer": answer_data["correct_answer"],
        "question_number": answer_data["question_number"],
        "total_questions": answer_data["total_questions"],
    }, room=QUIZ_ROOM)

    # Update and broadcast leaderboard
    leaderboard = get_leaderboard()
    socketio.emit("leaderboard_update", {
        "leaderboard": leaderboard
    }, room=QUIZ_ROOM)

    logger.info(f"📊 Leaderboard updated with {len(leaderboard)} participants")


def _finish_quiz(socketio):
    """End the quiz and broadcast final results."""
    end_quiz()
    cancel_all_timers()

    # Get final leaderboard
    leaderboard = get_leaderboard()

    # Broadcast quiz finished with final leaderboard
    socketio.emit("quiz_finished", {
        "message": "The quiz has ended!",
        "leaderboard": leaderboard
    }, room=QUIZ_ROOM)

    logger.info("🏁 Quiz finished! Final leaderboard broadcasted.")
