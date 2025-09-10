import os
import bcrypt

from typing import Optional
from Backend.repository.clinic_repo import validate_credentials
from Backend.core.security import create_clinic_token
from Database.db_register import Clinic
from fastapi import Request
from starlette.responses import HTMLResponse, RedirectResponse
from Database.db_register import SessionLocal, Clinic
from sqlalchemy.exc import IntegrityError
from Backend.core.security import verify_secret,hash_secret

COOKIE_NAME = "access_token"
IS_SECURE = False
class AuthController:
    def index(self,):
        current_dir = os.path.dirname(__file__)
        project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))  # D:\Work\TechFestAsaADatChatu
        template_path = os.path.join(project_root, 'Frontend', 'auth.html')
        print(template_path)
        with open(template_path, 'r', encoding='utf-8') as file:
            html_content = file.read()
        return HTMLResponse(content=html_content, status_code=200)
    

    async def login(self, request: Request):
        #return "<h1>AAAA</h1>"
        if request.method != 'POST':
            return RedirectResponse(url="/auth/index")
        
        form = await request.form()
        email = form.get('email') or ''
        password = form.get('password') or ''
        print(f"id={email}, password={password}")

        if Clinic.authenticate(email, password):
            token = create_clinic_token(clinic_email = email, clinic_name = Clinic.get_clinic_name(email), plan="standard")
            resp = RedirectResponse(url="/home/index", status_code=302)
            resp.set_cookie(
                COOKIE_NAME,
                token,
                httponly=False,
                secure=IS_SECURE,
                samesite="Lax",
                max_age=60 * 60 * 24,  # cookie lifetime (not JWT lifetime)
                path="/",
            )
            
            return resp
        
        return HTMLResponse("""
            <script>
              alert("Invalid username or password");
              window.location.href = "/auth/index";
            </script>
        """)
    
    async def register(self, request: Request):
        if request.method != 'POST':
            return RedirectResponse(url="/auth/index")

        form = await request.form()
        clinic_name = (form.get('username') or '').strip()
        email = (form.get('email') or '').strip().lower()
        password = form.get('password') or ''

        if not clinic_name or not email or not password:
            return """
                <script>
                  alert("Please fill all fields.");
                  window.location.href = "/auth/index";
                </script>
            """

        # Hash the password before storing
        pwd_hash = hash_secret(password)

        try:
            with SessionLocal() as session:
                clinic = Clinic(
                    clinic_id=Clinic._new_id(),
                    name=clinic_name,
                    email=email,
                    password_hash=pwd_hash,
                )
                session.add(clinic)
                session.commit()

        except IntegrityError as e:
            # Optional: make messages smarter using e.orig (psycopg2) to detect constraint
            # For now, show generic duplicate message.
            return """
                <script>
                  alert("User already exists (username or email).");
                  window.location.href = "/auth/index";
                </script>
            """
        except Exception:
            return """
                <script>
                  alert("Registration failed due to a server error.");
                  window.location.href = "/auth/index";
                </script>
            """

        return HTMLResponse("""
            <script>
              alert("Registration successful! You can log in now.");
              window.location.href = "/auth/index";
            </script>
        """)

