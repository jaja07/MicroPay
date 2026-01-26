from pydantic import BaseModel, EmailStr

class SendOTPRequestUser(BaseModel):
    email: EmailStr

class VerifyOTPRequestUser(BaseModel):
    email: EmailStr
    otp_code: str

class MailBody(BaseModel):
    to: EmailStr
    subject: str
    body: str