from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class QueryRequest(BaseModel):
    message: str

@app.post("/query")
async def handle_query(data: QueryRequest):
    # Placeholder logic
    user_message = data.message
    return {"response": f"Received query: {user_message}"}

@app.post("/filter")
async def filter_messages(data: QueryRequest):
    # Placeholder logic
    message = data.message
    return {"filtered": f"Important part of: {message}"}
