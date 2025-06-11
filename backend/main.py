from fastapi import FastAPI
from .app.api import query, filter

app = FastAPI(
    title="Greenstein AI Backend",
    description="The core AI services for the Greenstein community platform.",
    version="0.1.0"
)

# Include routers
app.include_router(query.router, prefix="/query", tags=["Query"])
app.include_router(filter.router, prefix="/filter", tags=["Filter"])

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the Greenstein AI Backend"}
