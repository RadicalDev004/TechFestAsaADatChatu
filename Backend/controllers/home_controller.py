import os
from starlette.responses import HTMLResponse,RedirectResponse
from fastapi import Request
from Backend.core.security import get_current_session


class HomeController:
    async def index(self, request: Request):
        session = get_current_session(request)
        if not session:
            return RedirectResponse(url="/auth/index", status_code=302)

        current_dir = os.path.dirname(__file__)
        project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
        template_path = os.path.join(project_root, 'Frontend', 'home.html')
        with open(template_path, 'r', encoding='utf-8') as f:
            html = f.read()

        # Optional: prevent caching of protected pages
        resp = HTMLResponse(content=html, status_code=200)
        resp.headers["Cache-Control"] = "no-store"
        return resp