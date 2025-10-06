import ast
import os

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..ai_generator import generate_challenge_with_ai
from ..database.db import (
    get_challenge_quota,
    get_user_challenges,
    create_challenge_quota,
    reset_challenge_quota,
    create_challenge
)
from ..utils import authenticate_and_get_user_details
from ..database.models import get_db
import json
from datetime import datetime
from logging import getLogger
from ..hf_generator import CodingChallengeGenerator
from ..gemini_generator import generate_challenge_with_gemini_ai
from ..database import models

logger = getLogger(__name__)

router = APIRouter()


class ChallengeRequest(BaseModel):
    difficulty: str

    class Config:
        json_schema_extra = {"example": {"difficulty": "easy"}}


@router.post("/generate-challenge")
async def generate_challenge(request: ChallengeRequest, header: Request, db: Session = Depends(get_db)):
    try:
        user = authenticate_and_get_user_details(header)
        # user = authenticate_and_get_user_details(request)
        if not user:
            raise HTTPException(status_code=401, detail="Unauthorized")
        user_id = user.get("user_id")
        quota = get_challenge_quota(db, user_id)
        if not quota:
            quota = create_challenge_quota(db, user_id)
        quota = reset_challenge_quota(db, quota)
        if quota.quota_remaining <= 0:
            raise HTTPException(status_code=429, detail="Quota exhausted. Please try again later.")
        # Simulate challenge generation
        # api_key = os.getenv("HF_TOKEN")
        # generator = CodingChallengeGenerator(api_key="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")
        #
        # challenge_list = generator.generate_challenge(request.difficulty)
        # # Use the first challenge
        # challenge_data = challenge_list[0]

        # print(f'Generated challenge data: {challenge_data}')
        # challenge_data = generate_challenge_with_ai(request.difficulty)

        print(f"Using Gemini AI to generate challenge {request.difficulty} ...")
        challenge_data = generate_challenge_with_gemini_ai(request.difficulty)

        print(f'Generated challenge data: {challenge_data}')
        new_challenge = create_challenge(
            db=db,
            difficulty=request.difficulty,
            created_by=user_id,
            title=challenge_data["title"],
            options=json.dumps(challenge_data["options"]),
            correct_answer_id=challenge_data["correct_answer_id"],
            explanation=challenge_data["explanation"] or ""
        )

        quota.quota_remaining -= 1
        db.commit()

        return {
            "id": new_challenge.id,
            "difficulty": new_challenge.difficulty,
            "title": new_challenge.title,
            "options": json.loads(new_challenge.options),
            "correct_answer_id": new_challenge.correct_answer_id,
            "explanation": new_challenge.explanation if new_challenge.explanation else "",
            "timestamp": new_challenge.created_at.isoformat()
        }

        #
        # return {
        #     "challenge": {
        #         "id": new_challenge.id,
        #         "difficulty": new_challenge.difficulty,
        #         "title": new_challenge.title,
        #         "options": json.loads(new_challenge.options),
        #         "correct_answer_id": new_challenge.correct_answer_id,
        #         "explanation": new_challenge.explanation if new_challenge.explanation else "",
        #         "timestamp": new_challenge.created_at.isoformat()
        #     },
        #     # "quota_remaining": quota.quota_remaining
        # }

    except Exception as e:
        print("Error generating challenge:", str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/my-history")
async def get_challenge_history(request: Request, db: Session = Depends(get_db)):
    user = authenticate_and_get_user_details(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    user_id = user.get("user_id")

    challenges = get_user_challenges(db, user_id)

    for challenge in challenges:
        options_str = challenge.options
        options_list = convert_options_to_list(options_str)
        challenge.options = options_list

    return {"challenges": challenges}



@router.get("/quota")
async def get_quota(request: Request, db: Session = Depends(get_db)):
    user = authenticate_and_get_user_details(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    user_id = user.get("user_id")

    quota = get_challenge_quota(db, user_id)
    if not quota:
        return {
            "user_id": user_id,
            "quota_remaining": 0,
            "last_reset_date": datetime.now()
        }
    quota = reset_challenge_quota(db, quota)
    return quota


def convert_options_to_list(options_str: str) -> list:
    """Safely converts options string (either set-like or list-like) into a list of strings."""
    if not options_str:
        return []

    # Format 2: Square brackets (JSON/Python list format)
    if options_str.startswith('[') and options_str.endswith(']'):
        try:
            # Safely evaluate the string to a list
            return ast.literal_eval(options_str)
        except (ValueError, SyntaxError):
            # Fallback for unexpected characters if literal_eval fails
            return [opt.strip().strip('"').strip("'") for opt in options_str.strip('[]').split(',')]

    # Format 1: Curly braces (set-like format)
    elif options_str.startswith('{') and options_str.endswith('}'):
        # Remove outer braces, split by comma, and clean up surrounding quotes
        options_list = [option.strip() for option in options_str.strip('{}').split(',')]
        return [opt.strip('"').strip("'") for opt in options_list]

    return [options_str] # Default case if it's a single, unformatted option
