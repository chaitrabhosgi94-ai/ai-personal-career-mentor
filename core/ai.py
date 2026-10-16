"""Gemini AI integration with safe local fallbacks."""

import os
from google import genai
from google.genai import types


def ask_ai(system_prompt, user_prompt, fallback):
    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    if not api_key:
        return fallback + "\n\n[Demo mode: Gemini API key not found.]"

    try:
        client = genai.Client(api_key=api_key)

        response = client.models.generate_content(
            model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.5,
            ),
        )

        return response.text or fallback

    except Exception as e:
        print("Gemini Error:", repr(e))
        return fallback + "\n\n[AI service unavailable; showing a fallback response.]"