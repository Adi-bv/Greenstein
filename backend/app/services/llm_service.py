import logging
import instructor
from openai import AsyncOpenAI, OpenAIError
from pydantic import BaseModel
from ..core.config import settings
from enum import Enum
from typing import Dict, Type, Union
from functools import lru_cache

from ..core.exceptions import LLMServiceError

logger = logging.getLogger(__name__)

class PromptStrategy(str, Enum):
    GENERAL_QA = "general_qa"
    SUMMARIZE = "summarize"
    EXTRACT_ACTIONS_JSON = "extract_actions_json"
    PERSONALIZE_RESPONSE = "personalize_response"
    CATEGORIZE_MESSAGE = "categorize_message"
    SUMMARIZE_INTERACTION_HISTORY = "summarize_interaction_history"
    MASTER_AGENT_PLANNER = "master_agent_planner"
    REACT_AGENT_STEP = "react_agent_step"
    REACT_AGENT_FINAL_ANSWER = "react_agent_final_answer"

PROMPT_TEMPLATES = {
    PromptStrategy.GENERAL_QA: {
        "system": (
            "You are a helpful AI assistant for the Greenstein community. "
            "Answer the user's question based on the provided context. "
            "Be concise and professional."
        ),
        "user": "Context:\n---\n{document_context}\n---\n\nQuestion: {user_query}",
    },
    PromptStrategy.SUMMARIZE: {
        "system": (
            "You are an expert in summarizing text. Provide a concise, "
            "neutral summary of the following content."
        ),
        "user": "{text_to_summarize}",
    },
    PromptStrategy.EXTRACT_ACTIONS_JSON: {
        "system": (
            "You are an expert in identifying action items. Analyze the text and "
            "extract a list of clear, actionable tasks. Your output must be a JSON "
            "object with a single key 'action_items' containing a list of strings."
        ),
        "user": "Please extract action items from this text:\n\n{text_to_analyze}",
    },
    PromptStrategy.PERSONALIZE_RESPONSE: {
        "system": (
            "You are a helpful AI assistant for the Greenstein community. "
            "Answer the user's question based on the provided context. "
            "Personalize your response using the user's interests and past interactions. "
            "Be friendly, concise, and professional."
        ),
        "user": (
            "Context:\n---\n{document_context}\n---\n\n"
            "User Profile:\n- Interests: {user_interests}\n- Past Interactions Summary: {user_interaction_summary}\n\n"
            "Question: {user_query}"
        ),
    },
    PromptStrategy.CATEGORIZE_MESSAGE: {
        "system": (
            "You are an expert in message classification. Categorize the following text "
            "into one of the predefined categories. Your output must be a JSON object "
            "with a single key 'category' and a value from the allowed list."
        ),
        "user": "Please categorize this text:\n\n{text_to_categorize}",
    },
    PromptStrategy.SUMMARIZE_INTERACTION_HISTORY: {
        "system": (
            "You are an expert in summarizing conversations. Condense the following "
            "interaction history into a concise, third-person narrative summary. "
            "Focus on the key topics discussed and decisions made."
        ),
        "user": "Please summarize the following interaction history:\n\n{interaction_history}",
    },
    PromptStrategy.MASTER_AGENT_PLANNER: {
        "system": (
            "You are a master agent that orchestrates tasks by selecting the appropriate tool. "
            "Based on the user's request and the list of available tools, you must decide which tool to use. "
            "Your output must conform to the provided JSON schema, specifying the tool's name and the arguments to pass to it. "
            "The 'reasoning' field should briefly explain your choice. The 'args' field must be a dictionary of arguments for the chosen tool."
        ),
        "user": (
            "Available Tools:\n---\n{tool_descriptions}\n---\n\nUser Request: {user_request}"
        ),
    },
    PromptStrategy.REACT_AGENT_STEP: {
        "system": (
            "You are a reasoning agent that solves user requests by breaking them down into steps. "
            "You have access to a set of tools and must follow the ReAct (Reason, Act, Observe) framework. "
            "At each step, your response MUST be a single JSON object that validates against the ReActStep schema. "
            "It must contain three fields: 'thought', 'tool_name', and 'args'."
            "\n\n**RULES:**\n"
            "1. **thought**: A string explaining your reasoning for the current step.\n"
            "2. **tool_name**: The name of the tool to use, or 'finish' to end the task.\n"
            "3. **args**: A dictionary of arguments for the tool. If a tool needs no arguments, provide an empty dictionary: `{}`.\n"
            "4. **Input Handling**: If a tool's description indicates it requires a block of text as input (e.g., an argument named 'text'), you MUST use the content provided in the 'User Objective' for that argument. Do not make up text.\n"
            "\n**EXAMPLE:**\n"
            "If the user asks to summarize a report, and you have a 'summarize_text' tool that takes a 'text' argument, your response should look like this:\n"
            "```json\n"
            "{\n"
            "  \"thought\": \"The user wants a summary. I have the text of the report. I should use the summarize_text tool to generate the summary.\",\n"
            "  \"tool_name\": \"summarize_text\",\n"
            "  \"args\": {\n"
            "    \"text\": \"The sales report shows a 10% increase...\"\n"
            "  }\n"
            "}\n"
            "```\n"
            "When you have the final answer, you MUST use the 'finish' tool. Your response should look like this:\n"
            "```json\n"
            "{\n"
            "  \"thought\": \"I have successfully summarized the text and have the final answer.\",\n"
            "  \"tool_name\": \"finish\",\n"
            "  \"args\": {\n"
            "    \"answer\": \"The key points of the sales report are...\"\n"
            "  }\n"
            "}\n"
            "```"
        ),
        "user": (
            "Available Tools:\n---\n{tool_descriptions}\n---\n\nUser Objective: {user_request}\n\n" 
            "# Previous Steps (Thought, Action, Observation):\n{scratchpad}"
        ),
    },
    PromptStrategy.REACT_AGENT_FINAL_ANSWER: {
        "system": (
            "You are a reasoning agent that has attempted to solve a user's request but has reached the maximum number of steps. "
            "Your task is to provide a final, best-effort answer based on the work you have done so far. "
            "Analyze the user's objective and the history of your thoughts, actions, and observations in the scratchpad. "
            "Synthesize this information into a coherent and helpful response. "
            "If you have a clear result, state it. If you were stuck, explain the difficulty and provide a partial answer if possible."
        ),
        "user": (
            "User Objective: {user_request}\n\n"
            "Your Work History (Scratchpad):\n---\n{scratchpad}\n---\n\n"
            "Based on your work, what is the final answer?"
        ),
    },
}

class LLMService:
    def __init__(self, api_key: str, timeout: int):
        # Patch the client to add instructor's features
        self.client = instructor.patch(AsyncOpenAI(api_key=api_key, timeout=timeout))

    async def generate_response(
        self,
        strategy: PromptStrategy,
        context: Dict[str, str],
        model: str | None = None,
        response_model: Type[BaseModel] = None,
    ) -> Union[str, BaseModel]:
        model = model or settings.LLM_MODEL
        template = PROMPT_TEMPLATES.get(strategy)
        if not template:
            raise LLMServiceError("Invalid prompt strategy selected.")

        try:
            system_prompt = template["system"]
            user_prompt = template["user"].format(**context)
        except KeyError as e:
            msg = f"Missing key '{e.args[0]}' in context for strategy '{strategy.name}'"
            logger.error(msg)
            raise LLMServiceError(msg)

        logger.debug("--- LLM Request ---")
        logger.debug(f"Strategy: {strategy.name}")
        logger.debug(f"System Prompt: {system_prompt}")
        logger.debug(f"User Prompt: {user_prompt}")
        if response_model:
            logger.debug(f"Response Model: {response_model.__name__}")

        try:
            response_kwargs = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            }
            if response_model:
                response_kwargs["response_model"] = response_model

            response = await self.client.chat.completions.create(**response_kwargs)

            logger.debug("--- LLM Response ---")
            if response_model:
                logger.debug(f"Raw Response (pydantic model): {response.model_dump_json(indent=2)}")
            else:
                logger.debug(f"Raw Response (text): {response.choices[0].message.content.strip()}")

            if response_model:
                return response
            else:
                return response.choices[0].message.content.strip()

        except OpenAIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise LLMServiceError(f"An error occurred with the AI service: {e}")

@lru_cache()
def get_llm_service() -> LLMService:
    return LLMService(api_key=settings.OPENAI_API_KEY, timeout=settings.LLM_TIMEOUT)
