import os
import bcrypt
from typing import Optional


from fastapi import Request
from starlette.responses import HTMLResponse, RedirectResponse


class AuthenticatorController:
    def index(self,):
        return {"message": "This is the index page from the authenticator controller."}

