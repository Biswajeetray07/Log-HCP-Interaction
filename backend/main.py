import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import engine, Base
from app.models.interaction import Interaction   # noqa: F401 — needed for table creation
from app.api.routes import interaction, chat

# Create tables if they don't exist yet (no migration tool for now)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI CRM — HCP Interaction Module")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # tighten this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(interaction.router, prefix="/interactions", tags=["interactions"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])


@app.get("/")
async def root():
    return {"message": "API is running"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
