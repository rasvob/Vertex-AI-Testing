import os

import google.auth
from dotenv import load_dotenv
from google.auth.exceptions import DefaultCredentialsError
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv(override=True)  # Load environment variables from .env file, allowing overrides

SYSTEM_PROMPT = """You are an AI education assistant. Your sole purpose is to explain \
how Artificial Intelligence works - covering topics such as machine learning, deep learning, \
neural networks, training and inference, large language models (LLMs), reinforcement learning, \
generative AI, and related concepts.

If the user asks about anything unrelated to AI, politely let them know that you can only \
discuss AI topics and invite them to ask an AI-related question instead.

Keep your explanations clear, accurate, and approachable for a general audience unless the \
user explicitly asks for a more technical deep-dive."""

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        ("human", "{question}"),
    ]
)


def _as_bool(value: str | None) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _build_llm() -> ChatGoogleGenerativeAI:
    model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    use_vertex = _as_bool(os.environ.get("GOOGLE_GENAI_USE_VERTEXAI"))
    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")

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
                return ChatGoogleGenerativeAI(
                    model=model,
                    google_api_key=api_key,
                    vertexai=False,
                )
            raise EnvironmentError(
                "Vertex AI mode is enabled, but Application Default Credentials (ADC) "
                "were not found. Run `gcloud auth application-default login` or set "
                "GOOGLE_GENAI_USE_VERTEXAI=false and configure GOOGLE_API_KEY."
            ) from exc

        return ChatGoogleGenerativeAI(
            model=model,
            project=project,
            location=location,
            vertexai=True,
        )

    if not api_key:
        raise EnvironmentError(
            "GOOGLE_API_KEY (or GEMINI_API_KEY) is not set. Add it to your .env file."
        )
    return ChatGoogleGenerativeAI(
        model=model,
        google_api_key=api_key,
        vertexai=False,
    )


llm = _build_llm()
chain = prompt | llm | StrOutputParser()


def main() -> None:
    print("=" * 60)
    print("  AI Explainer Chatbot  (powered by Gemini via LangChain)")
    print("  Ask me anything about how Artificial Intelligence works.")
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

        response = chain.invoke({"question": user_input})
        print(f"\nBot: {response}\n")


if __name__ == "__main__":
    main()
