# main.py
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from Backend.utils.router import Router
from Backend.api.auth import router as auth_router
from starlette.responses import Response, HTMLResponse, RedirectResponse, StreamingResponse

app = FastAPI(title="Clinic Auth – MVP")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth_router, prefix="/api/auth")

# Our dynamic router
router = Router()

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

# Catch-all: delegate non-/api and non-/static paths to our custom Router
@app.api_route("/{full_path:path}", methods=["GET", "POST"], response_class=HTMLResponse)
async def handle_request(full_path: str, request: Request):
    path = f"/{full_path}" if full_path else "/"

    #Default route: redirect / -> /auth/register
    if path == "/":
        return RedirectResponse(url="/auth/index", status_code=303)

    # Block /api and /static here (the real APIs are mounted via include_router)
    if path.startswith("/api") or path.startswith("/static"):
        html = f"Page not found: {path} <br> <a href='/home/index'>Go to Home</a>"
        return HTMLResponse(content=html, status_code=404)

    result = await router.route(path, request=request)

    # tuple (content, status)
    if isinstance(result, tuple) and len(result) == 2 and isinstance(result[0], (str, bytes)) and isinstance(result[1], int):
        return HTMLResponse(content=result[0], status_code=result[1])

    # already a Starlette/FastAPI Response? pass through
    if isinstance(result, (Response, HTMLResponse, RedirectResponse, StreamingResponse)):
        return result

    # plain string/bytes -> wrap
    if isinstance(result, (str, bytes)):
        return HTMLResponse(content=result, status_code=200)

    # dict / pydantic / etc. -> let FastAPI serialize
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        reload=True,
    )
