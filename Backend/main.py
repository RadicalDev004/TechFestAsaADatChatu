from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.auth import router as auth_router

app = FastAPI(title="Clinic Auth – MVP")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

app.include_router(auth_router)

@app.get("/healthz")
def healthz():
    return {"status": "ok"}