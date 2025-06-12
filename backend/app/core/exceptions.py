class LLMServiceError(Exception):
    """Custom exception for errors related to the LLM service."""
    pass

class RAGServiceError(Exception):
    """Custom exception for errors related to the RAG service."""
    pass

class AgentError(Exception):
    """Custom exception for errors related to the Master Agent's operation."""
    pass
