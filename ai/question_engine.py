import inspect
from sarvamai import SarvamAI
from config import Config
from utils.sanitization import sanitize_model_output

def get_client():
    return SarvamAI(api_subscription_key=Config.SARVAM_API_KEY)

def _chat_completions(client, **kwargs):
    signature = inspect.signature(client.chat.completions)
    if "model" in signature.parameters:
        return client.chat.completions(**kwargs)
    kwargs.pop("model", None)
    return client.chat.completions(**kwargs)

def generate_question(role, answer=None, question_history=None, resume_text=None, language="English"):
    client = get_client()

    history_text = ""
    if question_history:
        history_text = "\n\nPrevious Q&A:\n"
        for i, qa in enumerate(question_history, 1):
            history_text += f"Q{i}: {qa.get('question', '')}\nA{i}: {qa.get('answer', '')}\n"

    resume_context = ""
    if resume_text:
        resume_context = f"\n\nCandidate's Resume/Experience:\n{resume_text}\n"

    language_instruction = f"Respond ONLY in {language}."

    if answer:
        prompt = f"""You are a professional AI interviewer.
Role: {role}
{resume_context}
{history_text}
The candidate just answered: "{answer}"

Based on their answer and their resume, ask ONE follow-up interview question.
{language_instruction}
Return ONLY the question text."""
    else:
        prompt = f"""You are a professional AI interviewer.
Role: {role}
{resume_context}

Start the interview with a warm greeting and ask your first question based on their resume if provided.
{language_instruction}
Return ONLY the greeting + question text."""

    response = _chat_completions(
        client,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        top_p=1,
        max_tokens=500,
        model=Config.SARVAM_CHAT_MODEL,
    )

    return sanitize_model_output(response.choices[0].message.content)
