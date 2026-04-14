import os
import json
from openai import OpenAI

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))

COACH_SYSTEM_PROMPT = """You are an AI bootcamp coach for a high school AI program called DataNativ Studio.
Your job is to help students build their first recommendation app over 4 weeks.
Your tone is: supportive, intellectually serious, and direct. Think of yourself as a great mentor — not a tutor who gives answers, but a coach who asks the right questions.

Style rules:
- Ask reflective questions that push students to think deeper
- Encourage specificity — vague ideas become weak apps
- Push students to simplify when they overcomplicate things
- Avoid overly technical jargon — speak to a smart high schooler
- When you give feedback, always end with 1 actionable suggestion
- Keep responses concise: 2-4 paragraphs max
"""

def ai_refine_idea(project_type: str, problem: str, target_user: str, features: list) -> str:
    try:
        prompt = f"""A student is building a {project_type} app.
Problem: {problem}
Target user: {target_user}
Features they want: {', '.join(features)}

Give them honest, specific feedback on their project idea. What's strong? What needs more specificity? 
Ask them 1-2 reflective questions to push them further. End with one concrete suggestion to improve."""
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": COACH_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            max_tokens=400
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI feedback unavailable right now. Error: {str(e)}"


def ai_week1_feedback(problem_statement: str, user_persona: str, why_recommendations: str) -> str:
    try:
        prompt = f"""A student is completing Week 1 of their AI bootcamp project.
Problem statement: {problem_statement}
User persona: {user_persona}  
Why recommendations help: {why_recommendations}

Give specific feedback on:
1. Is the problem statement specific enough?
2. Is the user persona real and detailed?
3. Is the case for recommendations compelling?
Ask one question to push them deeper. Give one specific improvement."""
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": COACH_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            max_tokens=400
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI feedback unavailable: {str(e)}"


def ai_week2_feedback(input_questions: str, recommendation_logic: str, scoring_factors: str) -> str:
    try:
        prompt = f"""A student defined their recommendation logic for Week 2.
Input questions they ask users: {input_questions}
Recommendation logic: {recommendation_logic}
Scoring factors: {scoring_factors}

Evaluate:
1. Are the inputs specific and useful?
2. Is the logic clear and explainable?
3. Are the scoring factors fair and balanced?
Push them to simplify or improve one thing. Ask one tough question."""
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": COACH_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            max_tokens=400
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI feedback unavailable: {str(e)}"


def ai_explain_code(code_block: str, section_name: str) -> str:
    try:
        prompt = f"""Explain this code block called "{section_name}" to a high school student who is new to coding.
Make it friendly, specific, and under 150 words. No jargon. Tell them:
1. What this code does
2. Which part they can change and why it matters

Code:
{code_block}"""
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a friendly coding teacher for high school students. Explain code simply and specifically."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=250
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Explanation unavailable: {str(e)}"


def ai_generate_pitch(project_type: str, problem: str, target_user: str, features: list, 
                       recommendation_logic: str, test_feedback: str) -> str:
    try:
        prompt = f"""Write a 60-second demo-day pitch for a high school student's AI project.

Project: {project_type}
Problem solved: {problem}
Target user: {target_user}
Key features: {', '.join(features)}
How it works: {recommendation_logic}
User test feedback: {test_feedback}

Write a compelling pitch that:
- Starts with a hook (relatable problem)
- Explains what the app does in plain language
- Shows the recommendation logic briefly
- Ends with impact/vision
Keep it under 150 words. Sound confident but not corporate."""
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You write punchy, inspiring pitch scripts for teenage entrepreneurs."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Pitch generation unavailable: {str(e)}"


def ai_week4_feedback(feedback_notes: str, improvements: str, project_type: str) -> str:
    try:
        prompt = f"""A student completed testing their {project_type} app.
User feedback they received: {feedback_notes}
Improvements they made: {improvements}

Give them feedback on:
1. Did they gather meaningful test feedback?
2. Were their improvements specific and user-focused?
3. What's the strongest part of their project?
End with encouragement and one final polish tip."""
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": COACH_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            max_tokens=350
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI feedback unavailable: {str(e)}"


def ai_enhance_recommendation(recommendation_result: dict, project_type: str, user_inputs: dict) -> str:
    try:
        prompt = f"""A student's {project_type} app recommended the following based on user inputs.
User inputs: {json.dumps(user_inputs, indent=2)}
Top recommendation: {json.dumps(recommendation_result, indent=2)}

Write a friendly 2-3 sentence explanation of WHY this is the top recommendation.
Speak directly to the user. Make it specific to their inputs. Sound like a knowledgeable friend."""
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You write friendly, specific explanations for recommendation apps targeting high school students."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150
        )
        return response.choices[0].message.content
    except Exception as e:
        return "This recommendation was selected based on how well it matches your profile and goals."
