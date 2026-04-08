# import httpx
# import asyncio
# import json
# import logging
# import os
# from dotenv import load_dotenv
# load_dotenv(override=True)

# logger = logging.getLogger("automation")

# async def generate_faqs_for_page(page_name: str, page_content: str, page_url: str) -> list:
    
#     api_key = os.getenv("ANTHROPIC_API_KEY")
#     if not api_key:
#         logger.warning("ANTHROPIC_API_KEY not set — skipping FAQ generation")
#         return []

#     prompt = f"""You are an SEO expert. Based on this webpage content, generate 4 FAQ questions and answers that people would search for. These will be used as FAQ schema to help this page appear in ChatGPT and Perplexity answers.

# Rules:
# - Questions must be natural and conversational
# - Answers must be 2-3 sentences max
# - Base answers strictly on the provided content
# - Return ONLY valid JSON, no extra text, no markdown backticks

# Format:
# {{"faqs": [{{"question": "...", "answer": "..."}}, {{"question": "...", "answer": "..."}}]}}

# Page Name: {page_name}
# Page URL: {page_url}
# Page Content: {page_content}
# """

#     res = None
#     async with httpx.AsyncClient() as client:
#         try:
#             res = await client.post(
#                 "https://api.anthropic.com/v1/messages",
#                 headers={
#                     "x-api-key": api_key,
#                     "anthropic-version": "2023-06-01",
#                     "content-type": "application/json"
#                 },
#                 json={
#                     "model": "claude-sonnet-4-20250514",
#                     "max_tokens": 1000,
#                     "messages": [{"role": "user", "content": prompt}]
#                 },
#                 timeout=30
#             )
            
#             logger.info(f"FAQ API response status: {res.status_code}")
            
#             data = res.json()
            
#             # Check for API errors
#             if "error" in data:
#                 logger.warning(f"FAQ API error for {page_url}: {data['error']}")
#                 return []
            
#             if "content" not in data:
#                 logger.warning(f"FAQ API unexpected response for {page_url}: {data}")
#                 return []

#             text = data["content"][0]["text"]
#             clean = text.replace("```json", "").replace("```", "").strip()
#             parsed = json.loads(clean)
#             return parsed.get("faqs", [])

#         except Exception as e:
#             logger.warning(f"FAQ generation failed for {page_url}: {e}")
#             logger.warning(f"API response: {res.text if res is not None else 'no response'}")
#             return []


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


# def generate_faq_schema_sync(page_name: str, page_content: str, page_url: str) -> dict:
#     """Use this in Celery tasks"""
#     faqs = asyncio.run(generate_faqs_for_page(page_name, page_content, page_url))
#     if not faqs:
#         return {}
#     return build_faq_schema(faqs, page_url)

# import os
# import json
# import logging
# import asyncio
# import textwrap
# # import google.generativeai as genai
# from google import genai
# # from google.genai import types

# logger = logging.getLogger("automation")

# # Configure Gemini
# client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))



# # -------------------------------
# # Core Gemini Call (sync)
# # -------------------------------
# def _generate_with_gemini(prompt: str) -> list:
#     try:
#         response = client.models.generate_content(
#             model='gemini-2.5-flash',
#             contents=prompt,
#             config=types.GenerateContentConfig(
#                 temperature=0,
#                 top_p=0.95,
#                 top_k=20,
#             ),
#         )

#         if not response or not response.text:
#             logger.warning("Empty response from Gemini")
#             return []

#         text = response.text.strip()

#         # Clean markdown if present
#         # clean = text.replace("```json", "").replace("```", "").strip()

#         # parsed = json.loads(clean)
#         import re

#         match = re.search(r"```json(.*?)```", text, re.DOTALL)
#         clean = match.group(1).strip() if match else text
#         parsed = json.loads(clean)

#         return parsed.get("faqs", [])

#     except Exception as e:
#         logger.exception("Gemini error")
#         return []


# # -------------------------------
# # Async Wrapper
# # -------------------------------
# async def generate_faqs_for_page(page_name: str, page_content: str, page_url: str) -> list:

#     if not os.getenv("GEMINI_API_KEY"):
#         logger.warning("GEMINI_API_KEY not set")
#         return []

#     prompt = f"""
# You are an SEO expert.

# Generate 4 FAQ questions and answers based strictly on the webpage content.

# Rules:
# - Questions must be natural and conversational
# - Answers must be 2-3 sentences max
# - Do NOT add extra info
# - Return ONLY valid JSON

# Format:
# {{"faqs": [{{"question": "...", "answer": "..."}}]}}

# Page Name: {page_name}
# Page URL: {page_url}
# Page Content: {page_content}
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

#     faqs = asyncio.run(generate_faqs_for_page(page_name, page_content, page_url))

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

from google import genai
from google.genai import types
from google.genai import errors as genai_errors

logger = logging.getLogger("automation")

# Free tier: 5 requests/min = 1 every 12 seconds
_RATE_LIMIT_DELAY = 12
_MAX_RETRIES = 3


# -------------------------------
# Core Gemini Call (sync)
# -------------------------------
def _generate_with_gemini(prompt: str, retry_count: int = 0) -> list:
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.warning("Missing GEMINI_API_KEY")
            return []

        client = genai.Client(api_key=api_key)

        # Rate limit delay to avoid 429 on free tier
        time.sleep(_RATE_LIMIT_DELAY)

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.4,
            ),
        )

        if not response or not getattr(response, "text", None):
            logger.warning("Empty response from Gemini")
            return []

        text = response.text.strip()

        # -------------------------------
        # Robust JSON Extraction
        # -------------------------------
        match = re.search(r'\{[\s\S]*"faqs"[\s\S]*\}', text, re.DOTALL)
        if not match:
            logger.warning("No JSON found in response")
            return []

        try:
            parsed = json.loads(match.group(0))
        except json.JSONDecodeError:
            logger.warning("Invalid JSON format from Gemini")
            return []

        faqs = parsed.get("faqs", [])

        # -------------------------------
        # Basic Validation
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

    except genai_errors.ClientError as e:
        # Handle rate limit (429) with smart retry
        if hasattr(e, 'status_code') and e.status_code == 429:
            if retry_count >= _MAX_RETRIES:
                logger.warning(f"Rate limit hit {_MAX_RETRIES} times, giving up")
                return []

            # Extract retry delay from error message
            retry_delay = 60  # default fallback
            try:
                match = re.search(r"'retryDelay': '(\d+)s'", str(e))
                if match:
                    retry_delay = int(match.group(1)) + 5  # add buffer
            except Exception:
                pass

            logger.warning(f"Rate limited by Gemini. Waiting {retry_delay}s before retry {retry_count + 1}/{_MAX_RETRIES}...")
            time.sleep(retry_delay)
            return _generate_with_gemini(prompt, retry_count=retry_count + 1)

        logger.exception("Gemini API error")
        return []

    except Exception:
        logger.exception("Gemini error")
        return []


# -------------------------------
# Async Wrapper
# -------------------------------
async def generate_faqs_for_page(page_name: str, page_content: str, page_url: str) -> list:

    if not os.getenv("GEMINI_API_KEY"):
        logger.warning("GEMINI_API_KEY not set")
        return []

    # Truncate cleanly without cutting mid-sentence
    content_preview = page_content[:4000]
    if len(page_content) > 4000:
        content_preview += "..."

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

    return await asyncio.to_thread(_generate_with_gemini, prompt)


# -------------------------------
# Fallback (VERY IMPORTANT)
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
# Schema Builder
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
# Sync Entry (Celery / Tasks)
# -------------------------------
def generate_faq_schema_sync(page_name: str, page_content: str, page_url: str) -> dict:

    try:
        faqs = asyncio.run(
            generate_faqs_for_page(page_name, page_content, page_url)
        )
    except RuntimeError:
        # Handles already running event loop (common in FastAPI)
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