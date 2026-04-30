from pydantic import BaseModel, Field, field_validator
from typing import List, Optional

class QuestionRequest(BaseModel):
    role: str = Field(default="Software Developer", min_length=2, max_length=100)
    answer: Optional[str] = Field(default=None, max_length=5000)
    question_history: List[dict] = Field(default_factory=list)

    @field_validator("question_history")
    @classmethod
    def validate_history(cls, v):
        for item in v:
            if not isinstance(item, dict) or "question" not in item:
                raise ValueError("Each history item must be a dict with a 'question' key")
        return v

class ReportRequest(BaseModel):
    role: str = Field(default="Software Developer", min_length=2, max_length=100)
    qa_history: List[dict] = Field(default_factory=list)
    room_id: Optional[str] = Field(default=None, min_length=1, max_length=50)

    @field_validator("qa_history")
    @classmethod
    def validate_qa_history(cls, v):
        for item in v:
            if not isinstance(item, dict) or "question" not in item or "answer" not in item:
                raise ValueError("Each QA history item must be a dict with 'question' and 'answer' keys")
        return v

class CreateInterviewRequest(BaseModel):
    room_id: Optional[str] = Field(default=None, min_length=1, max_length=50)
    role: str = Field(default="Software Developer", min_length=2, max_length=100)
    candidate_name: str = Field(default="Candidate", min_length=1, max_length=100)
    duration: int = Field(default=10, ge=1, le=60)

class SaveAnswersRequest(BaseModel):
    answers: str = Field(..., min_length=1, max_length=10000)
