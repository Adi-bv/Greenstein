from typing import Dict, List

from .base_tool import BaseTool
from .summarization_tool import SummarizationTool
from .action_extraction_tool import ActionExtractionTool
from .categorization_tool import CategorizationTool
from ..services.llm_service import LLMService, get_llm_service
from fastapi import Depends

class ToolRegistry:
    """A registry to manage and access all available agentic tools."""

    def __init__(self, llm_service: LLMService):
        self._tools = self._load_tools(llm_service)

    def _load_tools(self, llm_service: LLMService) -> Dict[str, BaseTool]:
        """Initializes and returns a dictionary of all available tools."""
        tools: List[BaseTool] = [
            SummarizationTool(llm_service),
            ActionExtractionTool(llm_service),
            CategorizationTool(llm_service),
        ]
        return {tool.name: tool for tool in tools}

    def get_tool(self, name: str) -> BaseTool | None:
        """Retrieves a tool by its name."""
        return self._tools.get(name)

    def get_all_tools(self) -> List[BaseTool]:
        """Returns a list of all registered tool instances."""
        return list(self._tools.values())

    def get_tool_descriptions(self) -> str:
        """Generates a formatted string of all tool names and descriptions for the master agent's prompt."""
        base_descriptions = "\n".join(
            f"- `{tool.name}`: {tool.description}" for tool in self.get_all_tools()
        )
        # Add the special 'finish' tool description for the ReAct loop
        finish_description = "- `finish`: Use this tool to return the final answer to the user. The 'answer' argument should be a complete, user-facing response."
        return f"{base_descriptions}\n{finish_description}"

# Dependency injector for the ToolRegistry
def get_tool_registry(llm_service: LLMService = Depends(get_llm_service)) -> ToolRegistry:
    # This could be cached with lru_cache if tool loading were expensive
    return ToolRegistry(llm_service)
