from pydantic import BaseModel, Field
from typing import List

from .base_tool import BaseTool
from ..services.llm_service import LLMService, PromptStrategy
from ..core.exceptions import LLMServiceError

# Define the Pydantic model for the structured response, co-located with the tool
class ActionItems(BaseModel):
    action_items: List[str] = Field(..., description="A list of clear, actionable tasks extracted from the text.")

class ActionExtractionTool(BaseTool):
    """A tool to extract a list of action items from a given text."""

    def __init__(self, llm_service: LLMService):
        self._llm_service = llm_service

    @property
    def name(self) -> str:
        return "extract_action_items"

    @property
    def description(self) -> str:
        return "Extracts a list of clear, actionable tasks from a given block of text. Use this when a user wants to know what the next steps or action items are."

    async def execute(self, text: str) -> ActionItems:
        """
        Executes the action item extraction task.

        Args:
            text: The text to be analyzed.

        Returns:
            An ActionItems object containing the list of extracted tasks.
        
        Raises:
            LLMServiceError: If the extraction fails.
        """
        if not text or not text.strip():
            raise ValueError("Input text cannot be empty.")

        try:
            # Use the instructor-powered service to get a structured response
            action_items_response = await self._llm_service.generate_response(
                strategy=PromptStrategy.EXTRACT_ACTIONS_JSON,
                context={"text_to_analyze": text},
                response_model=ActionItems
            )
            return action_items_response
        except LLMServiceError as e:
            raise e
