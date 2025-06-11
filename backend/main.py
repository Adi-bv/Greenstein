from fastapi import FastAPI
from .app.api import query, filter

app = FastAPI()

# Include routers
app.include_router(query.router, prefix="/query", tags=["query"])
app.include_router(filter.router, prefix="/filter", tags=["filter"])

@app.get("/")
async def root():
    return {"message": "Welcome to Greenstein API"}
