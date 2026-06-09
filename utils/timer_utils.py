"""
utils/timer_utils.py
---------------------
Timer utility functions for quiz phase management.
Provides helpers for scheduling phase transitions using eventlet greenthreads.
"""

import logging
import eventlet

logger = logging.getLogger(__name__)

# Track active timers so they can be cancelled
_active_timers = {}


def schedule_phase_transition(phase_name: str, delay_seconds: float, callback, *args):
    """
    Schedule a callback to run after a delay using eventlet.
    Cancels any existing timer with the same phase_name.
    
    Args:
        phase_name: Unique identifier for this timer (e.g., 'intro', 'answering')
        delay_seconds: Number of seconds to wait
        callback: Function to call when timer expires
        *args: Arguments to pass to the callback
    """
    # Cancel existing timer for this phase if any
    cancel_timer(phase_name)

    def _timer_task():
        try:
            eventlet.sleep(delay_seconds)
            logger.info(f"⏰ Timer expired: {phase_name} ({delay_seconds}s)")
            callback(*args)
        except Exception as e:
            logger.error(f"Timer error ({phase_name}): {e}")
        finally:
            # Clean up reference
            _active_timers.pop(phase_name, None)

    # Spawn the timer in a green thread
    timer_thread = eventlet.spawn(_timer_task)
    _active_timers[phase_name] = timer_thread
    logger.info(f"⏱️ Timer scheduled: {phase_name} ({delay_seconds}s)")


def cancel_timer(phase_name: str):
    """
    Cancel an active timer by its phase name.
    
    Args:
        phase_name: The identifier of the timer to cancel
    """
    timer = _active_timers.pop(phase_name, None)
    if timer:
        timer.cancel()
        logger.info(f"🚫 Timer cancelled: {phase_name}")


def cancel_all_timers():
    """Cancel all active timers."""
    for name in list(_active_timers.keys()):
        cancel_timer(name)
    logger.info("All timers cancelled")


def get_active_timers() -> list:
    """Get list of currently active timer names."""
    return list(_active_timers.keys())
