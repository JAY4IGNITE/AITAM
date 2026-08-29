from pydantic import BaseModel, Field
from typing import List, Optional

class QuizOption(BaseModel):
    id: str
    text: str

class QuizQuestion(BaseModel):
    id: str
    question: str
    options: List[QuizOption]
    correct_option_id: str
    explanation: str

class EducationModule(BaseModel):
    id: str
    title: str
    category: str
    difficulty: str  # Beginner, Intermediate, Advanced
    summary: str
    key_indicators: List[str]
    prevention_tips: List[str]
    real_world_example: str
    quizzes: List[QuizQuestion] = Field(default_factory=list)

class QuizAnswerSubmission(BaseModel):
    question_id: str
    selected_option_id: str

class QuizSubmissionRequest(BaseModel):
    module_id: str
    answers: List[QuizAnswerSubmission]

class QuizQuestionResult(BaseModel):
    question_id: str
    selected_option_id: str
    correct_option_id: str
    is_correct: bool
    explanation: str

class QuizSubmissionResponse(BaseModel):
    module_id: str
    score: int
    total: int
    percentage: float
    passed: bool
    results: List[QuizQuestionResult]
