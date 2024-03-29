from fastapi import APIRouter, status, Depends, HTTPException, Request, BackgroundTasks
from api.schemas_user import RegisterUserRequest, BaseFields
from database import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
import CRUD
from library.security_lib import PasswordEncrypt
from library.email_sender import send_email_verification

router = APIRouter(
    prefix='/api/user',
    tags=["Users", "API"]
)


@router.post('/create', status_code=status.HTTP_201_CREATED)
async def create_user_account(
        request: Request,
        background_tasks: BackgroundTasks,
        new_user: RegisterUserRequest,
        session: AsyncSession = Depends(get_async_session),
) -> BaseFields:

    is_email_already_taken = await CRUD.get_user_by_email(new_user.email, session)
    if is_email_already_taken:
        raise HTTPException(detail=f'User with email {new_user.email} already exists',
                            status_code=status.HTTP_403_FORBIDDEN)

    hashed_password = await PasswordEncrypt.get_password_hash(new_user.password)

    saved_user = await CRUD.create_user(
        name=new_user.name,
        email=new_user.email,
        hashed_password=hashed_password,
        image_url='',
        image_file='standard_icon.jpg',
        session=session
    )
    background_tasks.add_task(
        send_email_verification,
        user_email=saved_user.email,
        user_uuid=saved_user.user_uuid,
        user_name=saved_user.name,
        host=request.base_url,
        is_web=False
    )
    return new_user


@router.get("/verify/{user_uuid}")
async def verify_user_account(user_uuid: str, session: AsyncSession = Depends(get_async_session)) -> dict:
    user = await CRUD.verify_user_account(user_uuid, session)
    # return HTMLResponse(f"<h1 style='font-family: verdana'>{user.name}, your account has been verified </h1>") на веб
    return {'user': user.name, 'verified': True}
