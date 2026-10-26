from fastapi import FastAPI
from app.api.chat import router as chat_router
from app.api.profiles import router as profiles_router

app = FastAPI(title="Sydney Transit AI")

# Mount the chat router under the /api prefix
app.include_router(chat_router, prefix="/api")
app.include_router(profiles_router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)