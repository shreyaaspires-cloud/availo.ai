import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.contract import ContractStatus, ContractSignerRole


class ContractSignatureResponse(BaseModel):
    id: uuid.UUID
    contract_id: uuid.UUID
    user_id: uuid.UUID
    role_in_contract: ContractSignerRole
    signature_image_url: str
    signed_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ContractResponse(BaseModel):
    id: uuid.UUID
    booking_id: uuid.UUID
    content_html: str
    pdf_url: Optional[str] = None
    sha256_hash: Optional[str] = None
    status: ContractStatus
    generated_at: datetime
    created_at: datetime
    signatures: List[ContractSignatureResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class SignContractRequest(BaseModel):
    signature_image_base64: str = Field(..., description="Base64 encoded PNG signature")


class VerifyContractResponse(BaseModel):
    status: str
    stored_hash: Optional[str] = None
    provided_hash: str
