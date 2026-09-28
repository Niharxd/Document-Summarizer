"""
Cohere summarization client.

Provides domain-aware summary generation using the Cohere V2 API.
Reads COHERE_API_KEY from the .env file via python-dotenv.
"""
from __future__ import annotations

import os
from functools import lru_cache

import cohere
from dotenv import load_dotenv

load_dotenv()

MODEL = "command-a-plus-05-2026"

_DOMAIN_INSTRUCTIONS: dict[str, str] = {
    "legal": (
        "Summarize the following legal document. "
        "Focus on important clauses, obligations, rights, and conditions."
    ),
    "medical": (
        "Summarize the following medical document. "
        "Focus on diagnosis, findings, treatment, and important observations."
    ),
    "technical": (
        "Summarize the following technical document. "
        "Focus on architecture, methods, findings, and technical conclusions."
    ),
}

SUPPORTED_DOMAINS = frozenset(_DOMAIN_INSTRUCTIONS)


@lru_cache(maxsize=1)
def get_cohere_client() -> cohere.ClientV2:
    """Return a cached Cohere V2 client. Raises ValueError if API key is absent."""
    api_key = os.getenv("COHERE_API_KEY", "").strip()
    if not api_key:
        raise ValueError(
            "COHERE_API_KEY is not set. "
            "Copy .env.example to .env and add your key."
        )
    return cohere.ClientV2(api_key=api_key)


def build_domain_prompt(document_text: str, domain: str) -> str:
    """
    Return the full prompt string for the given domain.

    Raises
    ------
    ValueError
        If *domain* is not one of the supported domains.
    ValueError
        If *document_text* is empty or whitespace-only.
    """
    if not document_text or not document_text.strip():
        raise ValueError("document_text must not be empty.")
    if domain not in SUPPORTED_DOMAINS:
        raise ValueError(
            f"Unsupported domain '{domain}'. "
            f"Choose from: {sorted(SUPPORTED_DOMAINS)}"
        )
    instruction = _DOMAIN_INSTRUCTIONS[domain]
    return f"{instruction}\n\n{document_text.strip()}"


def generate_summary(document_text: str, domain: str) -> str:
    """
    Generate a domain-aware summary via the Cohere Chat API.

    Parameters
    ----------
    document_text : str
        Raw document text to summarize.
    domain : str
        One of 'legal', 'medical', 'technical'.

    Returns
    -------
    str
        The generated summary text.

    Raises
    ------
    ValueError
        For empty document, unsupported domain, or missing API key.
    RuntimeError
        If the Cohere API call fails.
    """
    prompt = build_domain_prompt(document_text, domain)  # validates inputs
    client = get_cohere_client()

    try:
        response = client.chat(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
        )
        for content_item in response.message.content:
            if getattr(content_item, "type", None) == "text":
                generated_text = getattr(content_item, "text", None)
                if isinstance(generated_text, str):
                    return generated_text
        raise RuntimeError("Cohere response did not contain a text content item.")
    except (ValueError, RuntimeError):
        raise
    except Exception as exc:
        raise RuntimeError(f"Cohere API call failed: {exc}") from exc
