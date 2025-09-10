import secrets
import os
from typing import Optional
from Backend.core.security import hash_secret, verify_secret
import time

from sqlalchemy import create_engine, Column, Integer, String, DateTime, func, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import OperationalError


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@db:5432/postgres"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,          # drops dead connections gracefully
    future=True
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()

class Clinic(Base):

    __tablename__ = 'clinics'
    __table_args__ = (
        UniqueConstraint("clinic_id", name="uq_user_username"),
        UniqueConstraint("email", name="uq_user_email"),
        CheckConstraint("char_length(clinic_id) = 6", name="ck_clinic_id_length"),
        CheckConstraint("clinic_id ~ '^[0-9a-f]{6}$'", name="ck_clinic_id_format"),
    )

    clinic_id= Column(String(6), primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    @staticmethod
    def _new_id() -> str:
        # 6 hex chars, lowercase (e.g., "70b5bd")
        return secrets.token_hex(3)

    @staticmethod
    def get_clinic_name(clinic_email: str) -> Optional[str]:
        session  = SessionLocal()
        try:
            clinic = session.query(Clinic).filter(Clinic.email == clinic_email).first()
            return clinic.name if clinic else None
        finally:
            session.close()

    @staticmethod
    def get_clinic_id_by_email(clinic_email: str) -> Optional[str]:
        session  = SessionLocal()
        try:
            clinic = session.query(Clinic).filter(Clinic.email == clinic_email).first()
            return clinic.clinic_id if clinic else None
        finally:
            session.close()

    @staticmethod
    def authenticate(clinic_email: str, password_plain: str) -> bool:
        session = SessionLocal()
        try:
            clinic = session.query(Clinic).filter(Clinic.email == clinic_email).first()
            if clinic and verify_secret(password_plain, clinic.password_hash):
                return True
            return False
        finally:
            session.close()

def init_db(max_retries: int = 30, delay_seconds: float = 1.0):
    # wait for DB to be truly reachable
    for attempt in range(1, max_retries + 1):
        try:
            Base.metadata.create_all(bind=engine)
            return
        except OperationalError as e:
            if attempt == max_retries:
                raise
            time.sleep(delay_seconds)


# if __name__ == "__main__":
#     ensure_table()
#     cid = register_clinic("Demo Clinic", "demo_password")
#     print("Registered clinic_id:", cid)
#     print("Auth OK?:", authenticate(cid, "demo_password"))
