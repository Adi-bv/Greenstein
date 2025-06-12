import json
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List
import logging

# Assuming llm_service is updated to support JSON mode and raise this custom exception
from app.services.llm_service import LLMService, PromptStrategy, get_llm_service
from app.core.exceptions import LLMServiceError

router = APIRouter()
logger = logging.getLogger(__name__)

# --- Reusable Pydantic Models ---
class TextRequest(BaseModel):
    text: str = Field(..., min_length=1)

class SummarizationResponse(BaseModel):
    summary: str

class ActionExtractionResponse(BaseModel):
    action_items: List[str]

class CategorizationResponse(BaseModel):
    category: str

# --- Summarization Agent ---
@router.post("/summarize", response_model=SummarizationResponse, tags=["Agents"])
async def summarize_text(request: TextRequest, llm_service: LLMService = Depends(get_llm_service)):
    """
    Accepts a block of text and returns a concise summary.
    This endpoint is now asynchronous.
    """
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")
    
    try:
        context = {"text_to_summarize": request.text}
        summary = await llm_service.generate_response(
            strategy=PromptStrategy.SUMMARIZE,
            context=context
        )
        return SummarizationResponse(summary=summary)
    except LLMServiceError as e:
        logger.error(f"LLM service error during summarization: {e}")
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during summarization: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal server error occurred.")

# --- Action Item Extraction Agent (with JSON mode) ---
@router.post("/extract-actions", response_model=ActionExtractionResponse, tags=["Agents"])
async def extract_action_items(request: TextRequest, llm_service: LLMService = Depends(get_llm_service)):
    """
    Accepts text and returns a list of action items, parsed reliably from JSON.
    This endpoint is now asynchronous and uses structured output.
    """
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")

    try:
        context = {"text_to_analyze": request.text}
        # Assuming the service is updated to handle the json_mode parameter
        json_response = await llm_service.generate_response(
            strategy=PromptStrategy.EXTRACT_ACTIONS_JSON,
            context=context,
            json_mode=True
        )
        
        # The LLM now returns a JSON string, which we can parse safely
        data = json.loads(json_response)
        action_items = data.get("action_items", [])
        
        if not isinstance(action_items, list) or not all(isinstance(item, str) for item in action_items):
            raise LLMServiceError("LLM returned malformed JSON for action items.")
            
        return ActionExtractionResponse(action_items=action_items)
    except json.JSONDecodeError:
        logger.error(f"Failed to decode JSON from LLM response: {json_response}")
        raise HTTPException(status_code=502, detail="Failed to parse action items from AI response.")
    except LLMServiceError as e:
        logger.error(f"LLM service error during action extraction: {e}")
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during action extraction: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal server error occurred.")

# --- Message Categorization Agent ---
@router.post("/categorize", response_model=CategorizationResponse, tags=["Agents"])
async def categorize_text(request: TextRequest, llm_service: LLMService = Depends(get_llm_service)):
    """
    Accepts a block of text and returns its category.
    This endpoint uses a specialized prompt for classification.
    """
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")

    try:
        context = {"text_to_categorize": request.text}
        json_response = await llm_service.generate_response(
            strategy=PromptStrategy.CATEGORIZE_MESSAGE,
            context=context,
            json_mode=True
        )
        
        data = json.loads(json_response)
        category = data.get("category")
        
        if not category or not isinstance(category, str):
            raise LLMServiceError("LLM returned malformed JSON for categorization.")
            
        return CategorizationResponse(category=category)
    except json.JSONDecodeError:
        logger.error(f"Failed to decode JSON from LLM response for categorization: {json_response}")
        raise HTTPException(status_code=502, detail="Failed to parse category from AI response.")
    except LLMServiceError as e:
        logger.error(f"LLM service error during categorization: {e}")
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during categorization: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal server error occurred.")
