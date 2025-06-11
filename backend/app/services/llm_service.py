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

PROMPT_TEMPLATES = {
    PromptStrategy.GENERAL_QA: {
        "system": "You are a helpful assistant for a community platform. Your goal is to provide clear, concise, and friendly answers based on the provided context.",
        "user": "Context:\n---\n{document_context}\n---\n\nQuestion: {user_query}\n\nAnswer:"
    },
    PromptStrategy.SUMMARIZE: {
        "system": "You are an expert summarizer. Your task is to create a concise and comprehensive summary of the provided text.",
        "user": "Please summarize the following text:\n\n{text_to_summarize}"
    },
    PromptStrategy.EXTRACT_ACTIONS_JSON: {
        "system": "You are an intelligent assistant. Analyze the text and extract key action items. Respond ONLY with a valid JSON object containing a single key 'action_items' which is a list of strings. Do not include any other text, explanation, or markdown formatting.",
        "user": "Please extract action items from this text:\n\n{text_to_analyze}"
    },
    PromptStrategy.PERSONALIZE_RESPONSE: {
        "system": "You are a helpful and friendly AI assistant for a community platform. Your goal is to provide clear, concise, and personalized answers. You must tailor your response based on the user's profile.",
        "user": "User Profile:\n- Interests: {user_interests}\n- Past Interactions Summary: {user_interaction_summary}\n\nContext:\n---\n{document_context}\n---\n\nQuestion: {user_query}\n\nPersonalized Answer:"
    }
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
