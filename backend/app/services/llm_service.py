import logging
from openai import AsyncOpenAI, OpenAIError
from ..core.config import settings
from enum import Enum
from typing import Dict
from functools import lru_cache

from .trust_service import sanitize_input
from ..core.exceptions import LLMServiceError

logger = logging.getLogger(__name__)

class PromptStrategy(Enum):
    GENERAL_QA = "general_qa"
    SUMMARIZE = "summarize"
    EXTRACT_ACTIONS_JSON = "extract_actions_json"
    PERSONALIZE_RESPONSE = "personalize_response"
    CATEGORIZE_MESSAGE = "categorize_message"

PROMPT_TEMPLATES = {
    PromptStrategy.GENERAL_QA: {
        "system": (
            "You are a highly precise and factual assistant for a community platform. "
            "Your primary directive is to answer user questions *exclusively* based on the provided context documents. "
            "Do not use any external knowledge. If the answer is not found in the context, "
            "you *must* state that you do not have enough information to answer and should not attempt to guess."
        ),
        "user": (
            "Context:\n---\n{document_context}\n---\n\n"
            "Based *only* on the context above, answer the following question:\n\n"
            "Question: {user_query}\n\n"
            "Answer:"
        ),
    },
    PromptStrategy.SUMMARIZE: {
        "system": (
            "You are a highly skilled text summarization engine. Your goal is to produce a neutral, "
            "objective, and concise summary of the given text, capturing only the main points and key "
            "information present. The summary should be a single, coherent paragraph."
        ),
        "user": "Please summarize the following text:\n\n{text_to_summarize}",
    },
    PromptStrategy.EXTRACT_ACTIONS_JSON: {
        "system": (
            "You are a specialized AI agent designed to extract actionable tasks from text. "
            "Your output must be a single, valid JSON object. This object should have one key, `action_items`, "
            "which holds a list of strings. Each string must be a clear action starting with a verb. "
            "Do not include any text, explanations, or markdown formatting outside of the JSON object."
        ),
        "user": "Please extract action items from this text:\n\n{text_to_analyze}",
    },
    PromptStrategy.PERSONALIZE_RESPONSE: {
        "system": (
            "You are a friendly and perceptive AI assistant. Your goal is to provide personalized answers "
            "based on the user's profile while adhering strictly to the provided context for factual information. "
            "Use the user's interests to frame the answer in a way that is relevant to them, but do *not* invent facts. "
            "If the answer is not in the context, state that clearly."
        ),
        "user": (
            "User Profile:\n- Interests: {user_interests}\n- Past Interactions Summary: {user_interaction_summary}\n\n"
            "Context Documents:\n---\n{document_context}\n---\n\n"
            "Based *only* on the context documents, but tailoring the tone for the user profile above, "
            "answer the following question:\n\n"
            "Question: {user_query}\n\n"
            "Personalized Answer:"
        ),
    },
    PromptStrategy.CATEGORIZE_MESSAGE: {
        "system": (
            "You are a message classification agent. Your task is to categorize the user's message into one of the "
            "following predefined categories: `Question`, `Announcement`, `Feedback`, `Bug Report`, or `General Chit-Chat`. "
            "Respond ONLY with a single JSON object containing one key, `category`, with the chosen category as its value."
        ),
        "user": "Please categorize the following message:\n\n{text_to_categorize}",
    },
}

class LLMService:
    def __init__(self, api_key: str, timeout: int):
        self.client = AsyncOpenAI(api_key=api_key, timeout=timeout)

    async def generate_response(
        self,
        strategy: PromptStrategy,
        context: Dict[str, str],
        model: str | None = None,
        json_mode: bool = False,
    ) -> str:
        model = model or settings.LLM_MODEL
        template = PROMPT_TEMPLATES.get(strategy)
        if not template:
            raise LLMServiceError("Invalid prompt strategy selected.")

        sanitized_context = {
            k: sanitize_input(v) if isinstance(v, str) else v
            for k, v in context.items()
        }

        try:
            system_prompt = template["system"]
            user_prompt = template["user"].format(**sanitized_context)
        except KeyError as e:
            msg = f"Missing key '{e.args[0]}' in context for strategy '{strategy.name}'"
            logger.error(msg)
            raise LLMServiceError(msg)

        try:
            response_kwargs = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            }
            if json_mode:
                response_kwargs["response_format"] = {"type": "json_object"}

            response = await self.client.chat.completions.create(**response_kwargs)
            return response.choices[0].message.content.strip()
        except OpenAIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise LLMServiceError(f"An error occurred with the AI service: {e}")

@lru_cache()
def get_llm_service() -> LLMService:
    return LLMService(api_key=settings.OPENAI_API_KEY, timeout=settings.LLM_TIMEOUT)
