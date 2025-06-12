from .base_tool import BaseTool
from ..services.llm_service import LLMService, PromptStrategy
from ..core.exceptions import LLMServiceError

class SummarizationTool(BaseTool):
    """A tool to generate a concise summary of a given text."""

    def __init__(self, llm_service: LLMService):
        self._llm_service = llm_service

    @property
    def name(self) -> str:
        return "summarize_text"

    @property
    def description(self) -> str:
        return "Generates a concise, neutral summary of a given block of text. Use this when a user asks for a summary or the main points of a long document."

    async def execute(self, text: str) -> str:
        """
        Executes the summarization task.

        Args:
            text: The text to be summarized.

        Returns:
            The generated summary as a string.
        
        Raises:
            LLMServiceError: If the summarization fails.
        """
        if not text or not text.strip():
            raise ValueError("Input text cannot be empty.")

        try:
            summary = await self._llm_service.generate_response(
                strategy=PromptStrategy.SUMMARIZE,
                context={"text_to_summarize": text}
            )
            return summary
        except LLMServiceError as e:
            # Re-raise to allow the master agent to handle it
            raise e
