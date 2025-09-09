from typing import List, Literal
from pydantic import BaseModel, ConfigDict, Field

class ClinicRegisterRequest(BaseModel):
    name: str
    password: str

class ClinicRegisterResponse(BaseModel):
    clinic_id: str
    name: str

class ClinicTokenRequest(BaseModel):
    clinic_id: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class ClinicPrincipal(BaseModel):
    clinic_id: str
    clinic_name: str
    plan: str = "standard"

class ConversationOut(BaseModel):
    id: int
    title: str
    model_config = ConfigDict(from_attributes=True)


class MessageIn(BaseModel):
    content: str = Field(min_length=1)


class MessageOut(BaseModel):
    id: int
    role: Literal["user", "assistant"]
    content: str
    model_config = ConfigDict(from_attributes=True)


class ConversationWithMessages(BaseModel):
    conversation: ConversationOut
    messages: List[MessageOut]
