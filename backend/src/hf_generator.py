import re

from huggingface_hub import InferenceClient
import os
import json


def extract_json(text: str):
    """
    Extract the first valid JSON object from LLM output.
    """
    try:
        # Match the first JSON object in the text
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            return {"error": "No JSON found", "raw": text}

        json_str = match.group(0).strip()

        # Try loading JSON
        return json.loads(json_str)
    except Exception as e:
        return {"error": f"JSON parsing failed: {str(e)}", "raw": text}


def parse_multiple_json_blocks(text: str):
    """
    Extracts all JSON objects from a string and parses them individually.
    Returns a list of dicts.
    """
    results = []
    # Match all {...} blocks
    matches = re.findall(r"\{[\s\S]*?\}", text)
    for m in matches:
        try:
            # Attempt to fix common issues: missing commas
            m_fixed = re.sub(r'("correct_answer_id"\s*:\s*\d+)\s+("explanation")', r'\1, \2', m)
            results.append(json.loads(m_fixed))
        except Exception as e:
            results.append({"error": f"JSON parsing failed: {str(e)}", "raw": m})
    return results



class CodingChallengeGenerator:
    def __init__(self, api_key: str = None, model: str = "HuggingFaceH4/zephyr-7b-beta"):
        self.api_key = api_key or os.getenv("HF_TOKEN")
        if not self.api_key:
            raise ValueError("Hugging Face API key is required. Set HF_TOKEN env variable or pass it directly.")
        self.client = InferenceClient(api_key=self.api_key)
        self.model = model

        self.system_prompt = """You are an expert coding challenge creator. 
        Your task is to generate a coding question with multiple choice answers.
        The question should be appropriate for the specified difficulty level.

        For easy questions: Focus on basic syntax, simple operations, or common programming concepts.
        For medium questions: Cover intermediate concepts like data structures, algorithms, or language features.
        For hard questions: Include advanced topics, design patterns, optimization techniques, or complex algorithms.

        Return the challenge in the following JSON structure:
        {
            "title": "The question title",
            "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
            "correct_answer_id": 0,
            "explanation": "Detailed explanation of why the correct answer is right, this is always mandatory"
        }

        Make sure the options are plausible but with only one clearly correct answer.
        """

    def generate_challenge(self, difficulty: str = "easy"):
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"Generate one {difficulty} coding challenge."}
        ]

        response = self.client.chat_completion(
            model=self.model,
            messages=messages,
            max_tokens=400,
            temperature=0.7
        )

        try:

            content = response.choices[0].message["content"]
            challenges = parse_multiple_json_blocks(content)
            print(f"Parsed Code {len(challenges)} challenges: {challenges}")
            return challenges

            # content = response.choices[0].message["content"]
            # start = content.find("{")
            # end = content.rfind("}") + 1
            #
            # # print(f"Raw model response: {content}")
            #
            # if start != -1 and end != -1:
            #     challenge_json = content[start:end]
            #     return json.loads(challenge_json)
            # else:
            #     return {"error": "Invalid response format", "raw": content}
        except Exception as e:
            return {"error": str(e), "raw": str(response)}

