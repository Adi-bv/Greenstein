from typing import Annotated, TypedDict, List
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

class ConversationState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    summary: str
    message_count: int
    response: str

def should_summarize(state: ConversationState):
    return state["message_count"] % 5 == 0

def summarize_messages(state: ConversationState):
    recent_messages = state["messages"][-5:]
    
    # Combine with previous summary if exists
    context = state["summary"] + "\n" if state["summary"] else ""
    context += "\n".join([msg.content for msg in recent_messages])
    
    # Generate new summary (replace with actual LLM call)
    new_summary = f"Summary of messages {state['message_count']-4}-{state['message_count']}:\n{context[:200]}..."
    
    # Generate response (replace with actual LLM call)
    response = f"Bot response based on: {new_summary[:100]}..."
    
    return {
        "summary": new_summary,
        "response": response,
        "message_count": state["message_count"] + 1
    }

def default_processing(state: ConversationState):
    return {"message_count": state["message_count"] + 1}

# Initialize workflow
workflow = StateGraph(ConversationState)
workflow.add_node("summarizer", summarize_messages)
workflow.add_node("counter", default_processing)

# Conditional edges
workflow.add_conditional_edges(
    "counter",
    should_summarize,
    {"summarize": "summarizer", "continue": "counter"}
)
workflow.add_edge("summarizer", "counter")

# Set entry point
workflow.set_entry_point("counter")
conversation_chain = workflow.compile()

# Example usage
initial_state = {
    "messages": [],
    "summary": "",
    "message_count": 0,
    "response": ""
}

# Simulate conversation
for i in range(1, 16):
    initial_state["messages"].append(f"User message {i}")
    result = conversation_chain.invoke(initial_state)
    
    if result["response"]:
        print(f"Bot Response at message {i}: {result['response']}")
        print(f"Current Summary: {result['summary']}\n")
