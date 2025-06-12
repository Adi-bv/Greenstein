from pydantic import BaseModel, Field
from enum import Enum

from .base_tool import BaseTool
from ..services.llm_service import LLMService, PromptStrategy
from ..core.exceptions import LLMServiceError

# Define the possible categories as an Enum for type safety
class MessageCategory(str, Enum):
    QUESTION = "Question"
    ANNOUNCEMENT = "Announcement"
    FEEDBACK = "Feedback"
    BUG_REPORT = "Bug Report"
    GENERAL_CHIT_CHAT = "General Chit-Chat"

# Define the Pydantic model for the structured response
class CategorizationResult(BaseModel):
    category: MessageCategory = Field(..., description="The most likely category for the given text.")

class CategorizationTool(BaseTool):
    """A tool to categorize a given text into a predefined set of categories."""

    def __init__(self, llm_service: LLMService):
        self._llm_service = llm_service

    @property
    def name(self) -> str:
        return "categorize_text"

    @property
    def description(self) -> str:
        return "Categorizes a block of text into one of the following: Question, Announcement, Feedback, Bug Report, or General Chit-Chat. Use this to understand the intent of a message."

    async def execute(self, text: str) -> CategorizationResult:
        """
        Executes the text categorization task.

        Args:
            text: The text to be categorized.

        Returns:
            A CategorizationResult object containing the determined category.
        
        Raises:
            LLMServiceError: If the categorization fails.
        """
        if not text or not text.strip():
            raise ValueError("Input text cannot be empty.")

        try:
            categorization_response = await self._llm_service.generate_response(
                strategy=PromptStrategy.CATEGORIZE_MESSAGE,
                context={"text_to_categorize": text},
                response_model=CategorizationResult
            )
            return categorization_response
        except LLMServiceError as e:
            raise e
