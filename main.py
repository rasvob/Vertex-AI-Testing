import os
import re

import google.auth
from dotenv import load_dotenv
from google.auth.exceptions import DefaultCredentialsError
from google import genai
from google.genai import errors, types

load_dotenv(override=True)  # Load environment variables from .env file, allowing overrides

SYSTEM_PROMPT = """You are an empathetic, non-judgmental, and compassionate mental health support companion. Your goal is to provide a safe space for the user to express their thoughts and feelings.

Core Guidelines:

Reflective Listening: Paraphrase what the user says to show you understand (e.g., "It sounds like you're feeling really overwhelmed by work right now.").

Validation: Validate their emotions without being dismissive. (e.g., "It makes sense that you would feel hurt by that.").

Curiosity, Not Advice: Do not rush to give advice or "fix" the problem. Instead, ask open-ended, probing questions to help the user explore their own feelings (e.g., "What do you think is making this specific situation so hard for you?").

Tone: Warm, calm, patient, and conversational. Avoid sounding clinical or robotic."""


def _as_bool(value: str | None) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _validate_developer_api_key(api_key: str) -> str:
    normalized = api_key.strip()
    blocked_prefixes = ("Bearer ", "ya29.", "auth_tokens/", "AQ.")

    if any(normalized.startswith(prefix) for prefix in blocked_prefixes):
        raise EnvironmentError(
            "GOOGLE_API_KEY looks like an OAuth/ephemeral token, not a Google API key. "
            "Use a real Gemini/Google API key for Developer API mode, or switch to "
            "Vertex mode with GOOGLE_GENAI_USE_VERTEXAI=true and ADC."
        )

    if not re.fullmatch(r"AIza[0-9A-Za-z_-]{20,}", normalized):
        raise EnvironmentError(
            "GOOGLE_API_KEY format looks invalid for Gemini Developer API. "
            "Expected a Google API key that typically starts with 'AIza'."
        )

    return normalized


def _build_client() -> tuple[genai.Client, str]:
    model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    use_vertex = _as_bool(os.environ.get("GOOGLE_GENAI_USE_VERTEXAI"))
    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")

    print(f"[startup] Using model: {model}")
    print(f"[startup] GOOGLE_GENAI_USE_VERTEXAI: {use_vertex}")

    if use_vertex:
        project = os.environ.get("GOOGLE_CLOUD_PROJECT")
        location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")

        if not project:
            raise EnvironmentError(
                "GOOGLE_CLOUD_PROJECT is required when GOOGLE_GENAI_USE_VERTEXAI=true."
            )

        try:
            google.auth.default()
        except DefaultCredentialsError as exc:
            if api_key:
                print(
                    "[startup] Vertex AI credentials not found. "
                    "Falling back to Gemini API key mode."
                )
                api_key = _validate_developer_api_key(api_key)
                return genai.Client(api_key=api_key), model
            raise EnvironmentError(
                "Vertex AI mode is enabled, but Application Default Credentials (ADC) "
                "were not found. Run `gcloud auth application-default login` or set "
                "GOOGLE_GENAI_USE_VERTEXAI=false and configure GOOGLE_API_KEY."
            ) from exc

        return (
            genai.Client(vertexai=True, project=project, location=location),
            model,
        )

    if not api_key:
        raise EnvironmentError(
            "GOOGLE_API_KEY (or GEMINI_API_KEY) is not set. Add it to your .env file."
        )
    api_key = _validate_developer_api_key(api_key)
    return genai.Client(api_key=api_key), model


def _generate_answer(client: genai.Client, model: str, question: str) -> str:
    response = client.models.generate_content(
        model=model,
        contents=question,
        config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
    )

    text = (response.text or "").strip()
    if text:
        return text
    return "I couldn't generate a text response for that prompt. Please try rephrasing."

client, model = _build_client()


def main() -> None:
    print("=" * 60)
    print("  Mental Health Support Companion  (powered by google-genai)")
    print("  A safe space to share thoughts and feelings.")
    print("  Warm, reflective listening with validating follow-up questions.")
    print("  Type 'quit' or 'exit' to end the session.")
    print("=" * 60)
    print()

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() in {"quit", "exit"}:
            print("Goodbye!")
            break

        try:
            response = _generate_answer(client, model, user_input)
        except errors.ClientError as exc:
            print(f"\nError: {exc}\n")
            continue

        print(f"\nBot: {response}\n")


if __name__ == "__main__":
    main()
