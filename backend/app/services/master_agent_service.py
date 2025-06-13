import logging
from pydantic import BaseModel, Field, ValidationError
from typing import Dict, Any
from fastapi import Depends

from .llm_service import LLMService, PromptStrategy, get_llm_service
from ..tools.tool_registry import ToolRegistry, get_tool_registry
from ..core.exceptions import AgentError, LLMServiceError

logger = logging.getLogger(__name__)

# Pydantic model for the structured output from the ReAct LLM call
class ReActStep(BaseModel):
    thought: str = Field(..., description="The agent's reasoning and plan for the next action.")
    tool_name: str = Field(..., description="The name of the tool to execute, or 'finish' to complete the task.")
    args: Dict[str, Any] = Field(default_factory=dict, description="The arguments for the chosen tool. For 'finish', this should be {'answer': '...'}.")

class MasterAgent:
    """The master agent, now powered by a ReAct loop for multi-step reasoning."""

    def __init__(self, llm_service: LLMService, tool_registry: ToolRegistry, max_steps: int = 5):
        self.llm_service = llm_service
        self.tool_registry = tool_registry
        self.max_steps = max_steps

    async def execute_task(self, user_request: str) -> Any:
        """
        Orchestrates a task using a ReAct loop (Reason, Act, Observe).

        Args:
            user_request: The user's initial request.

        Returns:
            The final answer from the agent.

        Raises:
            AgentError: If the agent fails to complete the task within the step limit or encounters an error.
        """
        logger.info(f"ReAct Agent starting task for request: '{user_request}'")
        scratchpad = ""
        tool_descriptions = self.tool_registry.get_tool_descriptions()

        for i in range(self.max_steps):
            logger.info(f"ReAct Step {i+1}/{self.max_steps}")
            observation = ""

            try:
                # 1. Reason: LLM generates a thought and an action plan (a ReActStep)
                react_step = await self.llm_service.generate_response(
                    strategy=PromptStrategy.REACT_AGENT_STEP,
                    context={
                        "tool_descriptions": tool_descriptions,
                        "user_request": user_request,
                        "scratchpad": scratchpad
                    },
                    response_model=ReActStep
                )

                thought = react_step.thought
                action = react_step.tool_name
                args = react_step.args

                scratchpad += f"\nThought: {thought}\nAction: {action} with args {args}"
                logger.debug(f"Scratchpad updated with new thought/action.")

                # 2. Act: Execute the planned action
                if action == "finish":
                    answer = args.get("answer", "I have completed the task.")
                    logger.info(f"ReAct agent finished with answer: {answer}")
                    return answer

                tool = self.tool_registry.get_tool(action)
                if not tool:
                    observation = f"Error: Tool '{action}' not found."
                else:
                    try:
                        tool_result = await tool.execute(**args)
                        observation = f"Observation: {tool_result}"
                    except Exception as e:
                        logger.error(f"Execution of tool '{action}' failed: {e}", exc_info=True)
                        observation = f"Error executing tool '{action}': {e}"

            except (LLMServiceError, ValidationError) as e:
                logger.error(f"Error in ReAct step {i+1}: {e}", exc_info=True)
                # This is a critical observation for the agent to self-correct
                observation = f"Error: My previous attempt failed with the error: '{e}'. I must carefully analyze the error and my previous steps to form a new, valid plan. I need to ensure my output is a valid JSON object conforming to the required schema."
            
            # 3. Observe: Add the result back to the scratchpad
            scratchpad += f"\n{observation}"
            logger.debug(f"Scratchpad updated with new observation.")

        logger.warning(f"ReAct agent reached max steps ({self.max_steps}). Attempting to generate a final answer.")
        try:
            final_answer = await self.llm_service.generate_response(
                strategy=PromptStrategy.REACT_AGENT_FINAL_ANSWER,
                context={
                    "user_request": user_request,
                    "scratchpad": scratchpad
                }
            )
            logger.info(f"Generated a final answer after max steps: {final_answer}")
            return final_answer
        except LLMServiceError as e:
            logger.error(f"Failed to generate a final answer after max steps: {e}", exc_info=True)
            raise AgentError("I could not complete the task within the allowed number of steps and also failed to generate a summary of my work.")

# Dependency injector for the MasterAgent
def get_master_agent(
    llm_service: LLMService = Depends(get_llm_service),
    tool_registry: ToolRegistry = Depends(get_tool_registry),
) -> MasterAgent:
    return MasterAgent(llm_service=llm_service, tool_registry=tool_registry)
