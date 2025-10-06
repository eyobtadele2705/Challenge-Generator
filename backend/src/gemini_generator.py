import os
import json
from google import genai
from google.genai import types  # For config types


def generate_challenge_with_gemini_ai(difficulty: str = 'medium'):  # Match your import name
    # Get API key (prefer env var for security; fallback to hardcoded for dev)
    api_key = os.environ.get("GEMINI_API_KEY", "AIzaSyA_SBC8OimddGZCbsqBt71xbRF2w16gKeU")

    # Initialize client with API key
    client = genai.Client(api_key=api_key)

    # User prompt (triggers generation)
    user_prompt = f"Generate a random {difficulty}-difficulty coding problem in Python."

    # System instruction (guides the model) - Minor tweak for grammar: added "-level" for clarity
    system_instruction = f"""
    You are an expert coding challenge creator. 
    Your task is to generate a {difficulty}-level coding question with multiple choice answers in Python.
    The question should be appropriate for the specified difficulty level.

    For easy questions: Focus on basic syntax, simple operations, or common programming concepts.
    For medium questions: Cover intermediate concepts like data structures, algorithms, or language features.
    For hard questions: Include advanced topics, design patterns, optimization techniques, or complex algorithms.

    Make sure the options are plausible but with only one clearly correct answer.
    """

    # Define the exact JSON schema to enforce structured output
    json_schema = {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "options": {"type": "array", "items": {"type": "string"}, "minItems": 4, "maxItems": 4},
            "correct_answer_id": {"type": "integer", "minimum": 0, "maximum": 3},
            "explanation": {"type": "string"}
        },
        "required": ["title", "options", "correct_answer_id", "explanation"]
    }

    try:
        response = client.models.generate_content(  # Note: client.models.generate_content is the method
            model="gemini-2.5-flash",
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",  # Enforces JSON output
                response_json_schema=json_schema,  # Ensures exact structure
                temperature=0.7,  # Balanced randomness
                max_output_tokens=512  # Increased to handle medium/hard (was 500)
            )
        )

        # Add handling for None response.text
        if response.text is None:
            # Log/debug the reason (e.g., MAX_TOKENS, SAFETY)
            if response.candidates and response.candidates[0].finish_reason:
                raise ValueError(f"Gemini generation failed: Finish reason = {response.candidates[0].finish_reason}")
            else:
                raise ValueError("Gemini response.text is None - check token limits or prompt feedback.")

        # Parse the JSON response
        challenge_data = json.loads(response.text)

        return challenge_data

    except Exception as e:
        raise ValueError(f"Error generating challenge with Gemini: {str(e)}")