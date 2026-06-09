"""
seed_data.py
-------------
Database seed script.
Populates the questions collection with 20 startup and
entrepreneurship questions for the quiz.

Usage:
    python seed_data.py
"""

import logging
from database.mongodb import get_db, init_db
from models.question_model import delete_all_questions, insert_questions, get_question_count

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# ── 20 Startup & Entrepreneurship Questions ────────────────────

SEED_QUESTIONS = [
    {
        "question": "Which entrepreneur founded Tesla, Inc.?",
        "options": ["Elon Musk", "Jeff Bezos", "Bill Gates", "Mark Zuckerberg"],
        "correct_answer": "Elon Musk"
    },
    {
        "question": "What does MVP stand for in startup terminology?",
        "options": ["Most Valuable Product", "Minimum Viable Product", "Major Value Proposition", "Maximum Viable Pitch"],
        "correct_answer": "Minimum Viable Product"
    },
    {
        "question": "Who founded Amazon?",
        "options": ["Larry Page", "Jeff Bezos", "Steve Jobs", "Sundar Pichai"],
        "correct_answer": "Jeff Bezos"
    },
    {
        "question": "A 'Unicorn Startup' is valued at over?",
        "options": ["$100 Million", "$500 Million", "$1 Billion", "$10 Billion"],
        "correct_answer": "$1 Billion"
    },
    {
        "question": "Who co-founded Apple Inc. with Steve Wozniak?",
        "options": ["Tim Cook", "Steve Jobs", "Bill Gates", "Larry Ellison"],
        "correct_answer": "Steve Jobs"
    },
    {
        "question": "Which funding round typically comes FIRST?",
        "options": ["Series A", "Seed", "Series B", "IPO"],
        "correct_answer": "Seed"
    },
    {
        "question": "What is 'Bootstrapping' in business?",
        "options": ["Using investor money", "Self-funding a startup", "Taking a bank loan", "Crowdfunding"],
        "correct_answer": "Self-funding a startup"
    },
    {
        "question": "Who founded SpaceX?",
        "options": ["Richard Branson", "Jeff Bezos", "Elon Musk", "Peter Thiel"],
        "correct_answer": "Elon Musk"
    },
    {
        "question": "What does 'B2B' stand for?",
        "options": ["Buyer to Buyer", "Business to Business", "Brand to Brand", "Bank to Business"],
        "correct_answer": "Business to Business"
    },
    {
        "question": "Founder of Facebook (Meta)?",
        "options": ["Mark Zuckerberg", "Jack Dorsey", "Evan Spiegel", "Kevin Systrom"],
        "correct_answer": "Mark Zuckerberg"
    },
    {
        "question": "Which is a Venture Capital firm?",
        "options": ["Sequoia Capital", "Goldman Sachs", "JP Morgan", "Visa"],
        "correct_answer": "Sequoia Capital"
    },
    {
        "question": "Founder of Flipkart?",
        "options": ["Ritesh Agarwal", "Sachin Bansal", "Bhavish Aggarwal", "Vijay Shekhar Sharma"],
        "correct_answer": "Sachin Bansal"
    },
    {
        "question": "OYO Rooms was founded by?",
        "options": ["Ritesh Agarwal", "Kunal Shah", "Deepinder Goyal", "Byju Raveendran"],
        "correct_answer": "Ritesh Agarwal"
    },
    {
        "question": "What is 'Pivot' in startup terms?",
        "options": ["Closing a startup", "Changing business strategy", "Hiring new staff", "Going public"],
        "correct_answer": "Changing business strategy"
    },
    {
        "question": "Who founded Microsoft?",
        "options": ["Steve Jobs", "Bill Gates", "Larry Page", "Jack Ma"],
        "correct_answer": "Bill Gates"
    },
    {
        "question": "Founder of Alibaba?",
        "options": ["Jack Ma", "Pony Ma", "Robin Li", "Lei Jun"],
        "correct_answer": "Jack Ma"
    },
    {
        "question": "ROI stands for?",
        "options": ["Rate Of Income", "Return On Investment", "Revenue Over Income", "Risk Of Investment"],
        "correct_answer": "Return On Investment"
    },
    {
        "question": "Founder of Paytm?",
        "options": ["Vijay Shekhar Sharma", "Kunal Shah", "Sachin Bansal", "Bhavish Aggarwal"],
        "correct_answer": "Vijay Shekhar Sharma"
    },
    {
        "question": "What is an 'Angel Investor'?",
        "options": ["Government grant", "Wealthy individual investing in startups", "Bank loan officer", "Crowdfunding platform"],
        "correct_answer": "Wealthy individual investing in startups"
    },
    {
        "question": "Founder of Ola Cabs?",
        "options": ["Bhavish Aggarwal", "Ritesh Agarwal", "Deepinder Goyal", "Kunal Shah"],
        "correct_answer": "Bhavish Aggarwal"
    },
]


def seed_questions():
    """Insert seed questions into the database."""
    # Initialize database and indexes
    init_db()

    # Check if questions already exist
    existing_count = get_question_count()
    if existing_count > 0:
        logger.info(f"ℹ️ {existing_count} questions already exist. Clearing and re-seeding...")
        delete_all_questions()

    # Insert seed questions
    count = insert_questions(SEED_QUESTIONS)
    logger.info(f"🎉 Successfully seeded {count} questions!")

    # Verify
    final_count = get_question_count()
    logger.info(f"Total questions in database: {final_count}")


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("  🌱 Quiz Database Seed Script")
    print("=" * 50 + "\n")
    seed_questions()
    print("\n✅ Seeding complete!\n")
