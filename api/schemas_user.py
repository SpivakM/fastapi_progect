from pydantic import BaseModel, Field, EmailStr


class BaseFields(BaseModel):
    email: EmailStr = Field(description="your email", examples=['example@gmail.com'])
    name: str = Field(description="your name", examples=['Mark Twen'])


class PasswordField(BaseModel):
    password: str = Field(description="your password", min_length=8)


class RegisterUserRequest(PasswordField, BaseFields):
    pass


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_at: int
    token_type: str = 'Bearer'
