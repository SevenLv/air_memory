"""FastAPI application entry point."""

from fastapi import FastAPI

from air_memory.api.router import router

app = FastAPI(title="AIR_Memory", version="1.0.0")

app.include_router(router)


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "ok"}
