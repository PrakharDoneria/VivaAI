import unittest
from pydantic import ValidationError
from utils.validation import QuestionRequest


class TestValidation(unittest.TestCase):
    def test_question_history_validation(self):
        with self.assertRaises(ValidationError):
            QuestionRequest(question_history=[{"bad": "shape"}])


if __name__ == '__main__':
    unittest.main()
