import unittest
from utils.sanitization import sanitize_model_output


class TestSanitization(unittest.TestCase):
    def test_removes_think_blocks(self):
        text = "Hi<think>secret</think>there"
        self.assertEqual(sanitize_model_output(text), "Hithere")


if __name__ == '__main__':
    unittest.main()
