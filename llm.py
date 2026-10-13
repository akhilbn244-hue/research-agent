"""
llm.py  -  THE ONLY FILE THAT TALKS TO GEMINI
=============================================

One function, think(), sends the conversation so far (plus the tool menu)
to Gemini and returns its reply. The reply is either:
  - a request to use one or more tools, or
  - finished text (the final report).

Same safety net as the other projects: wait and retry when Google is busy,
wait and switch model when the free tier's per-minute limit is hit.
"""

import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

MODELS = [
    os.getenv("GEMINI_MODEL"),
    "gemini-flash-latest",
    "gemini-2.5-flash",
    "gemini-flash-lite-latest",
]


class AIError(Exception):
    """A friendly error we show on screen instead of a crash."""


def get_api_key():
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key or key == "paste-your-key-here":
        raise AIError("No API key found. Open the .env file in this folder, paste your Gemini key after "
                      "GEMINI_API_KEY=, save it, and restart the app.")
    return key


def what_went_wrong(message):
    if any(sign in message for sign in ("503", "UNAVAILABLE", "500", "INTERNAL", "overloaded")):
        return "busy"
    if "404" in message or "not found" in message.lower():
        return "missing"
    if "429" in message or "RESOURCE_EXHAUSTED" in message:
        return "limit"
    if "API key" in message or "API_KEY" in message:
        return "bad_key"
    return "other"


def think(contents, system_prompt, tool_menu=None):
    """
    Send the conversation to Gemini. Returns (response, tokens_used).
    tool_menu: list of tool descriptions, or None to force a plain-text answer.
    """
    client = genai.Client(api_key=get_api_key())
    settings = types.GenerateContentConfig(
        system_instruction=system_prompt,
        temperature=0.3,
        tools=[types.Tool(function_declarations=[
            types.FunctionDeclaration(name=t["name"], description=t["description"], parameters_json_schema=t["parameters"])
            for t in tool_menu])] if tool_menu else None,
        # We run the tools ourselves, step by step, so we can show and control every action.
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
    )

    last_problem, last_kind = None, "other"
    for model in [m for m in MODELS if m]:
        for attempt in range(3):
            try:
                response = client.models.generate_content(model=model, contents=contents, config=settings)
                usage = response.usage_metadata
                return response, (getattr(usage, "total_token_count", 0) or 0)
            except Exception as problem:
                last_problem, last_kind = problem, what_went_wrong(str(problem))
                if last_kind == "busy" and attempt < 2:
                    time.sleep(2 * (attempt + 1))
                    continue
                if last_kind == "limit" and attempt == 0:
                    time.sleep(15)
                    continue
                if last_kind in ("busy", "missing", "limit"):
                    break
                if last_kind == "bad_key":
                    raise AIError("Gemini rejected your API key. Check it in .env (no spaces or quotes) and restart the app.")
                raise AIError(f"Gemini returned an error: {problem}")

    if last_kind == "limit":
        raise AIError("Gemini's free tier limit was reached on every model. Wait a few minutes, or try again tomorrow.")
    raise AIError(f"Gemini is busy right now. Wait a minute and try again. (Last error: {last_problem})")
