"""Import tất cả model để Base.metadata.create_all() nhận diện đầy đủ bảng."""
from models.user import User
from models.conversation import Conversation
from models.message import Message
from models.feedback import Feedback
from models.topic import Topic
from models.quiz import Quiz
from models.question import Question
from models.quiz_attempt import QuizAttempt
from models.submission import Submission
from models.topic_progress import TopicProgress

__all__ = [
    "User",
    "Conversation",
    "Message",
    "Feedback",
    "Topic",
    "Quiz",
    "Question",
    "QuizAttempt",
    "Submission",
    "TopicProgress",
]
