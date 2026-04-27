

# import os
# import json
# import logging
# import asyncio
# import textwrap
# import re
# import time

# from google import genai
# from google.genai import types
# from google.genai import errors as genai_errors

# logger = logging.getLogger("automation")

# # Free tier: 5 requests/min = 1 every 12 seconds
# _RATE_LIMIT_DELAY = 12
# _MAX_RETRIES = 3


# # -------------------------------
# # Core Gemini Call (sync)
# # -------------------------------
# def _generate_with_gemini(prompt: str, retry_count: int = 0) -> list:
#     try:
#         api_key = os.getenv("GEMINI_API_KEY")
#         if not api_key:
#             logger.warning("Missing GEMINI_API_KEY")
#             return []

#         client = genai.Client(api_key=api_key)

#         # Rate limit delay to avoid 429 on free tier
#         time.sleep(_RATE_LIMIT_DELAY)

#         response = client.models.generate_content(
#             model="gemini-2.5-flash",
#             contents=prompt,
#             config=types.GenerateContentConfig(
#                 temperature=0.4,
#             ),
#         )

#         if not response or not getattr(response, "text", None):
#             logger.warning("Empty response from Gemini")
#             return []

#         text = response.text.strip()

#         # -------------------------------
#         # Robust JSON Extraction
#         # -------------------------------
#         match = re.search(r'\{[\s\S]*"faqs"[\s\S]*\}', text, re.DOTALL)
#         if not match:
#             logger.warning("No JSON found in response")
#             return []

#         try:
#             parsed = json.loads(match.group(0))
#         except json.JSONDecodeError:
#             logger.warning("Invalid JSON format from Gemini")
#             return []

#         faqs = parsed.get("faqs", [])

#         # -------------------------------
#         # Basic Validation
#         # -------------------------------
#         valid_faqs = []
#         for faq in faqs:
#             if (
#                 isinstance(faq, dict)
#                 and "question" in faq
#                 and "answer" in faq
#                 and faq["question"].strip()
#                 and faq["answer"].strip()
#             ):
#                 valid_faqs.append(faq)

#         return valid_faqs

#     except genai_errors.ClientError as e:
#         # Handle rate limit (429) with smart retry
#         if hasattr(e, 'status_code') and e.status_code == 429:
#             if retry_count >= _MAX_RETRIES:
#                 logger.warning(f"Rate limit hit {_MAX_RETRIES} times, giving up")
#                 return []

#             # Extract retry delay from error message
#             retry_delay = 60  # default fallback
#             try:
#                 match = re.search(r"'retryDelay': '(\d+)s'", str(e))
#                 if match:
#                     retry_delay = int(match.group(1)) + 5  # add buffer
#             except Exception:
#                 pass

#             logger.warning(f"Rate limited by Gemini. Waiting {retry_delay}s before retry {retry_count + 1}/{_MAX_RETRIES}...")
#             time.sleep(retry_delay)
#             return _generate_with_gemini(prompt, retry_count=retry_count + 1)

#         logger.exception("Gemini API error")
#         return []

#     except Exception:
#         logger.exception("Gemini error")
#         return []


# # -------------------------------
# # Async Wrapper
# # -------------------------------
# async def generate_faqs_for_page(page_name: str, page_content: str, page_url: str) -> list:

#     if not os.getenv("GEMINI_API_KEY"):
#         logger.warning("GEMINI_API_KEY not set")
#         return []

#     # Truncate cleanly without cutting mid-sentence
#     content_preview = page_content[:4000]
#     if len(page_content) > 4000:
#         content_preview += "..."

#     prompt = f"""
# You are an SEO expert.

# Generate exactly 4 FAQ questions and answers strictly based on the webpage content.

# Rules:
# - Questions must be natural and user-focused
# - Answers must be concise (2-3 sentences max)
# - Do NOT hallucinate or add external info
# - Output ONLY valid JSON

# Format:
# {{
#   "faqs": [
#     {{"question": "...", "answer": "..."}}
#   ]
# }}

# Page Name: {page_name}
# Page URL: {page_url}
# Page Content: {content_preview}
# """

#     return await asyncio.to_thread(_generate_with_gemini, prompt)


# # -------------------------------
# # Fallback (VERY IMPORTANT)
# # -------------------------------
# def fallback_faqs(content: str) -> list:
#     return [
#         {
#             "question": "What is this page about?",
#             "answer": textwrap.shorten(content, width=200) if content else "This page provides relevant information on the topic."
#         },
#         {
#             "question": "Who should read this page?",
#             "answer": "Anyone looking for information related to this topic will find this page useful."
#         },
#         {
#             "question": "What information is covered here?",
#             "answer": "The page explains key details and insights related to the topic."
#         },
#         {
#             "question": "How can this information help me?",
#             "answer": "It helps you understand the topic and make informed decisions."
#         }
#     ]


# # -------------------------------
# # Schema Builder
# # -------------------------------
# def build_faq_schema(faqs: list, page_url: str) -> dict:
#     return {
#         "@context": "https://schema.org",
#         "@type": "FAQPage",
#         "url": page_url,
#         "mainEntity": [
#             {
#                 "@type": "Question",
#                 "name": faq["question"],
#                 "acceptedAnswer": {
#                     "@type": "Answer",
#                     "text": faq["answer"]
#                 }
#             }
#             for faq in faqs
#         ]
#     }


# # -------------------------------
# # Sync Entry (Celery / Tasks)
# # -------------------------------
# def generate_faq_schema_sync(page_name: str, page_content: str, page_url: str) -> dict:

#     try:
#         faqs = asyncio.run(
#             generate_faqs_for_page(page_name, page_content, page_url)
#         )
#     except RuntimeError:
#         # Handles already running event loop (common in FastAPI)
#         loop = asyncio.new_event_loop()
#         try:
#             faqs = loop.run_until_complete(
#                 generate_faqs_for_page(page_name, page_content, page_url)
#             )
#         finally:
#             loop.close()

#     if not faqs:
#         logger.warning("Using fallback FAQs")
#         faqs = fallback_faqs(page_content)

#     return build_faq_schema(faqs, page_url)

import os
import json
import logging
import asyncio
import textwrap
import re
import time

# ✅ CHANGED: Replaced `google.genai` imports with `groq`
from groq import Groq
from groq import RateLimitError, APIStatusError

logger = logging.getLogger("automation")

# ✅ CHANGED: Groq free tier allows ~30 req/min, so delay is much shorter
_RATE_LIMIT_DELAY = 2   # seconds between requests (was 12 for Gemini)
_MAX_RETRIES = 3

# ✅ CHANGED: Best Groq model for structured text generation.
# llama-3.3-70b-versatile → best quality/speed balance on Groq.
# Alternatives: "llama3-8b-8192" (faster, lighter), "mixtral-8x7b-32768" (longer context)
_GROQ_MODEL = "llama-3.3-70b-versatile"


# -------------------------------
# ✅ CHANGED: Core Groq Call (sync) — replaced _generate_with_gemini
# Everything else (JSON extraction, validation, retry logic) preserved.
# -------------------------------
def _generate_with_groq(prompt: str, retry_count: int = 0) -> list:
    try:
        api_key = os.getenv("GROQ_API_KEY")   # ✅ CHANGED: env var name
        if not api_key:
            logger.warning("Missing GROQ_API_KEY")
            return []

        # ✅ CHANGED: Groq client initialization
        client = Groq(api_key=api_key)

        # Rate limit delay
        time.sleep(_RATE_LIMIT_DELAY)

        # ✅ CHANGED: Groq uses OpenAI-compatible chat completions API
        response = client.chat.completions.create(
            model=_GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are an SEO expert. Always respond with valid JSON only. No markdown, no explanation."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.4,
            max_tokens=1024,
        )

        # ✅ CHANGED: Groq response structure (OpenAI-compatible)
        if not response or not response.choices:
            logger.warning("Empty response from Groq")
            return []

        text = response.choices[0].message.content
        if not text:
            logger.warning("Empty content in Groq response")
            return []

        text = text.strip()

        # -------------------------------
        # Robust JSON Extraction — UNCHANGED
        # -------------------------------
        match = re.search(r'\{[\s\S]*"faqs"[\s\S]*\}', text, re.DOTALL)
        if not match:
            logger.warning("No JSON found in response")
            return []

        try:
            parsed = json.loads(match.group(0))
        except json.JSONDecodeError:
            logger.warning("Invalid JSON format from Groq")
            return []

        faqs = parsed.get("faqs", [])

        # -------------------------------
        # Basic Validation — UNCHANGED
        # -------------------------------
        valid_faqs = []
        for faq in faqs:
            if (
                isinstance(faq, dict)
                and "question" in faq
                and "answer" in faq
                and faq["question"].strip()
                and faq["answer"].strip()
            ):
                valid_faqs.append(faq)

        return valid_faqs

    # ✅ CHANGED: Groq-specific exception handling
    # RateLimitError = 429, APIStatusError = other HTTP errors
    except RateLimitError as e:
        if retry_count >= _MAX_RETRIES:
            logger.warning(f"Rate limit hit {_MAX_RETRIES} times, giving up")
            return []

        # ✅ CHANGED: Groq returns Retry-After header; parse from error message if available
        retry_delay = 60  # default fallback
        try:
            # Groq error messages often contain "Please try again in Xs"
            match = re.search(r"try again in (\d+(\.\d+)?)s", str(e), re.IGNORECASE)
            if match:
                retry_delay = int(float(match.group(1))) + 5  # add buffer
        except Exception:
            pass

        logger.warning(
            f"Rate limited by Groq. Waiting {retry_delay}s before retry "
            f"{retry_count + 1}/{_MAX_RETRIES}..."
        )
        time.sleep(retry_delay)
        return _generate_with_groq(prompt, retry_count=retry_count + 1)

    except APIStatusError as e:
        # ✅ CHANGED: Handle other Groq API errors (500, 503, etc.)
        logger.exception(f"Groq API error (status {e.status_code}): {e.message}")
        return []

    except Exception:
        logger.exception("Groq error")
        return []


# -------------------------------
# ✅ CHANGED: Async wrapper — updated to call _generate_with_groq
# Signature and behavior UNCHANGED.
# -------------------------------
async def generate_faqs_for_page(page_name: str, page_content: str, page_url: str) -> list:

    if not os.getenv("GROQ_API_KEY"):   # ✅ CHANGED: env var name
        logger.warning("GROQ_API_KEY not set")
        return []

    # Truncate cleanly without cutting mid-sentence — UNCHANGED
    content_preview = page_content[:4000]
    if len(page_content) > 4000:
        content_preview += "..."

    # Prompt structure — UNCHANGED
    prompt = f"""
You are an SEO expert.

Generate exactly 4 FAQ questions and answers strictly based on the webpage content.

Rules:
- Questions must be natural and user-focused
- Answers must be concise (2-3 sentences max)
- Do NOT hallucinate or add external info
- Output ONLY valid JSON

Format:
{{
  "faqs": [
    {{"question": "...", "answer": "..."}}
  ]
}}

Page Name: {page_name}
Page URL: {page_url}
Page Content: {content_preview}
"""

    # ✅ CHANGED: Now calls _generate_with_groq instead of _generate_with_gemini
    return await asyncio.to_thread(_generate_with_groq, prompt)


# -------------------------------
# Fallback FAQs — UNCHANGED
# -------------------------------
def fallback_faqs(content: str) -> list:
    return [
        {
            "question": "What is this page about?",
            "answer": textwrap.shorten(content, width=200) if content else "This page provides relevant information on the topic."
        },
        {
            "question": "Who should read this page?",
            "answer": "Anyone looking for information related to this topic will find this page useful."
        },
        {
            "question": "What information is covered here?",
            "answer": "The page explains key details and insights related to the topic."
        },
        {
            "question": "How can this information help me?",
            "answer": "It helps you understand the topic and make informed decisions."
        }
    ]


# -------------------------------
# Schema Builder — UNCHANGED
# -------------------------------
def build_faq_schema(faqs: list, page_url: str) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "url": page_url,
        "mainEntity": [
            {
                "@type": "Question",
                "name": faq["question"],
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": faq["answer"]
                }
            }
            for faq in faqs
        ]
    }


# -------------------------------
# Sync Entry (Celery / Tasks) — UNCHANGED
# -------------------------------
def generate_faq_schema_sync(page_name: str, page_content: str, page_url: str) -> dict:

    try:
        faqs = asyncio.run(
            generate_faqs_for_page(page_name, page_content, page_url)
        )
    except RuntimeError:
        # Handles already running event loop (common in FastAPI) — UNCHANGED
        loop = asyncio.new_event_loop()
        try:
            faqs = loop.run_until_complete(
                generate_faqs_for_page(page_name, page_content, page_url)
            )
        finally:
            loop.close()

    if not faqs:
        logger.warning("Using fallback FAQs")
        faqs = fallback_faqs(page_content)

    return build_faq_schema(faqs, page_url)