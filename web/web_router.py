from fastapi import APIRouter, Request, Depends, BackgroundTasks, Form, UploadFile, File
from fastapi.templating import Jinja2Templates
from pathlib import Path
import CRUD
from database import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from library.security_lib import PasswordEncrypt, SecurityHandler
from library.email_sender import send_email_verification
from fastapi.responses import RedirectResponse
from starlette import status
from pydantic import EmailStr
import uuid


# скидання пароля через пошту, базова апі


web_router = APIRouter(
    prefix='',
    tags=['Web', 'Auth'],
    include_in_schema=False
)

templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / 'templates'))


async def get_form_data(request: Request):
    form = await request.form()
    return form


class UserCreateForm:
    def __init__(self, request: Request):
        self.request: Request = request
        self.errors: list = []
        self.email: Optional[str] = None
        self.name: Optional[str] = None
        self.password: Optional[str] = None
        self.password_confirm: Optional[str] = None
        self.hashed_password: str = ''
        self.image_url: str = ''
        self.image_file: UploadFile = File(None)
        self.image_file_name: str = 'standard_icon.jpg'

    async def load_data(self):
        form = await self.request.form()
        self.email = form.get('email')
        self.name = form.get('name')
        self.password = form.get('password')
        self.password_confirm = form.get('password_confirm')
        self.image_url = form.get('image_url')
        self.image_file = form.get('image_file')
        if self.image_file.filename:
            file_type = self.image_file.filename.split('.')[-1]
            if file_type in {"jpg", "png", "jpeg"}:
                self.image_file_name = f"{uuid.uuid4()}.{file_type}"
                with open(f'static/user_images/{self.image_file_name}', 'wb') as user_file:
                    user_file.write(await self.image_file.read())
            else:
                self.errors.append('Incorrect file type, must be .png, .jpg or .jpeg')

    async def is_valid(self, session: AsyncSession):
        if not self.email or '@' not in self.email:
            self.errors.append('Please? enter valid email')

        maybe_user = await CRUD.get_user_by_email(self.email, session)
        if maybe_user:
            self.errors.append('User with this email already exists')
        maybe_user = await CRUD.get_user_by_name(self.name, session)
        if maybe_user:
            self.errors.append('Name already taken')
        if not self.password or len(str(self.password)) < 8:
            self.errors.append('Please? enter password at least 8 symbols')
        if self.password != self.password_confirm:
            self.errors.append('Confirm password did not match!')
        if not self.errors:
            return True
        return False


class UserUpdateForm:
    def __init__(self, request: Request, user=Depends(SecurityHandler.get_current_user_web)):
        self.request: Request = request
        self.initial_user = user
        self.errors: list = []
        self.initial_email = user.email
        self.initial_name = user.name
        self.hashed_password = user.hashed_password
        self.initial_image_url = user.image_url
        self.initial_image_file_name = user.image_file
        self.new_name: Optional[str] = None
        self.new_email: Optional[str] = None
        self.password_confirm: Optional[str] = None
        self.new_image_url: Optional[str] = self.initial_image_url
        self.new_image_file: UploadFile = File(None)
        self.new_image_file_name: Optional[str] = self.initial_image_file_name

    async def load_data(self):
        form = await self.request.form()
        self.new_email = form.get('email')
        self.new_name = form.get('name')
        self.password_confirm = form.get('password')
        self.new_image_url = form.get('image_url')
        self.new_image_file = form.get('image_file')
        if self.new_image_file.filename:
            file_type = self.new_image_file.filename.split('.')[-1]
            if file_type in {"jpg", "png", "jpeg"}:
                self.new_image_file_name = f"{uuid.uuid4()}.{file_type}"
                with open(f'static/user_images/{self.new_image_file_name}', 'wb') as user_file:
                    user_file.write(await self.new_image_file.read())
            else:
                self.errors.append('Incorrect file type, must be .png, .jpg or .jpeg')

    async def is_valid(self, session: AsyncSession):
        if not self.new_email or '@' not in self.new_email:
            self.errors.append('Please? enter valid email')

        if self.new_email != self.initial_email:
            maybe_user = await CRUD.get_user_by_email(self.new_email, session)
            if maybe_user:
                self.errors.append('User with this email already exists')

        if self.new_name != self.initial_name:
            maybe_user = await CRUD.get_user_by_name(self.new_name, session)
            if maybe_user:
                self.errors.append('Name already taken')

        if not await PasswordEncrypt.verify_password(plain_password=self.password_confirm,
                                                     hashed_password=self.hashed_password):
            self.errors.append('Wrong password')
        if not self.errors:
            return True
        return False


class PostCreateForm:
    def __init__(self, request: Request, user_id: int):
        self.request: Request = request
        self.errors: list = []
        self.topic: Optional[str] = None
        self.text: Optional[str] = None
        self.category: Optional[str] = None
        self.user_id: user_id = user_id

    async def load_data(self):
        form = await self.request.form()
        self.topic = form.get('topic')
        self.text = form.get('text')
        self.category = form.get('category')

    async def is_valid(self, session: AsyncSession):
        maybe_user = await CRUD.get_user_by_id(self.user_id, session)
        if not maybe_user:
            self.errors.append('User does not exists')
        if not self.topic:
            self.errors.append('Please? enter topic')
        if len(str(self.topic)) > 50:
            self.errors.append('Topic must be less than 50 symbols')
        if not self.text:
            self.errors.append('Please? enter text')
        if len(str(self.text)) > 500:
            self.errors.append('Text must be less than 500 symbols')
        if not self.category:
            self.errors.append('Please? enter category')
        if len(str(self.category)) > 25:
            self.errors.append('Category must be less than 25 symbols')
        if not self.errors:
            return True
        return False


class PostEditForm:
    def __init__(self, request: Request):
        self.request: Request = request
        self.errors: list = []
        self.topic: Optional[str] = None
        self.text: Optional[str] = None
        self.category: Optional[str] = None
        self.post_id: Optional[int] = None

    async def load_data(self):
        form = await self.request.form()
        self.topic = form.get('edit_post_topic')
        self.text = form.get('edit_post_text')
        self.category = form.get('edit_post_category')
        self.post_id = int(form.get('post_id'))

    async def is_valid(self, session: AsyncSession):
        maybe_post = await CRUD.get_post_by_id(self.post_id, session)
        if not maybe_post:
            self.errors.append('Post does not exists')
        if not self.topic:
            self.errors.append('Please? enter topic')
        if len(str(self.topic)) > 50:
            self.errors.append('Topic must be less than 50 symbols')
        if not self.text:
            self.errors.append('Please? enter text')
        if len(str(self.text)) > 500:
            self.errors.append('Text must be less than 500 symbols')
        if not self.category:
            self.errors.append('Please? enter category')
        if len(str(self.category)) > 25:
            self.errors.append('Category must be less than 25 symbols')
        if not self.errors:
            return True
        return False


@web_router.get('/signup')
@web_router.post('/signup')
async def web_register(request: Request,
                       background_tasks: BackgroundTasks,
                       session: AsyncSession = Depends(get_async_session)):
    if request.method == 'GET':
        return templates.TemplateResponse('registration.html', context={'request': request})

    new_user_form = UserCreateForm(request)
    await new_user_form.load_data()
    if await new_user_form.is_valid(session):
        hashed_password = await PasswordEncrypt.get_password_hash(new_user_form.password)

        saved_user = await CRUD.create_user(
            name=new_user_form.name,
            email=new_user_form.email,
            hashed_password=hashed_password,
            image_url=new_user_form.image_url,
            image_file=new_user_form.image_file_name,
            session=session,
        )

        background_tasks.add_task(
            send_email_verification,
            user_email=saved_user.email,
            user_uuid=saved_user.user_uuid,
            user_name=saved_user.name,
            host=request.base_url,
            is_web=True
        )

        redirect_url = request.url_for('index')

        response = RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER)

        return await SecurityHandler.set_cookies_web(saved_user, response)
    else:

        return templates.TemplateResponse('registration.html', context=new_user_form.__dict__)


@web_router.get('/login', description='get form for login')
@web_router.post('/login', description='fill out the login form')
async def user_login_web(
        request: Request,
        email: EmailStr = Form(None),
        password: str = Form(None),
        session: AsyncSession = Depends(get_async_session),
):
    if request.method == 'GET':
        return templates.TemplateResponse('login.html', context={'request': request})

    user, is_password_correct = await SecurityHandler.authenticate_user_web(email, password or '', session)
    if all([user, is_password_correct]):
        redirect_url = request.url_for('index')
        response = RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER)
        return await SecurityHandler.set_cookies_web(user, response)
    return templates.TemplateResponse('login.html', context={'request': request})


@web_router.get('/logout', description='log out')
async def user_logout_web(request: Request):
    response = templates.TemplateResponse('login.html', context={'request': request})
    response.delete_cookie(key='token')
    return response


@web_router.get('/verify_account')
@web_router.post('/verify_account')
async def verify_account_web(request: Request, background_tasks: BackgroundTasks,
                             user=Depends(SecurityHandler.get_current_user_web), ):
    content = {'request': request, 'user': user}
    if request.method == 'GET':
        if not user.verified:
            background_tasks.add_task(
                send_email_verification,
                user_email=user.email,
                user_uuid=user.user_uuid,
                user_name=user.name,
                host=request.base_url,
                is_web=True
            )
        return templates.TemplateResponse('verify_account.html', context=content)


@web_router.get('/add-post')
@web_router.post('/add-post')
async def add_post_web(request: Request,
                       user=Depends(SecurityHandler.get_current_user_web),
                       session: AsyncSession = Depends(get_async_session)):
    content = {'request': request, 'user': user}
    if not user:
        response = templates.TemplateResponse('login.html', context=content)
        return response

    if not user.verified:
        response = templates.TemplateResponse('verify_account.html', context=content)
        return response

    if user.verified:
        if request.method == 'GET':
            response = templates.TemplateResponse('add_post.html', context=content)
            return response
        new_post_form = PostCreateForm(request=request, user_id=user.id)
        await new_post_form.load_data()
        if await new_post_form.is_valid(session=session):
            await CRUD.create_post(session=session,
                                   topic=new_post_form.topic,
                                   text=new_post_form.text,
                                   category=new_post_form.category,
                                   user_id=new_post_form.user_id)

        else:
            new_post_form.__dict__['user'] = user

            return templates.TemplateResponse('add_post.html', context=new_post_form.__dict__)

        redirect_url = request.url_for('index')
        response = RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER)
        return response


@web_router.get('/edit-post')
@web_router.post('/edit-post')
async def edit_post_web(request: Request,
                        user=Depends(SecurityHandler.get_current_user_web),
                        session: AsyncSession = Depends(get_async_session)):
    content = {
        'request': request,
        'user': user,
    }
    if not user:
        response = templates.TemplateResponse('login.html', context=content)
        return response

    if not user.verified:
        response = templates.TemplateResponse('verify_account.html', context=content)
        return response

    if user.verified:
        if request.method == 'GET':
            response = templates.TemplateResponse('edit_post.html', context=content)
            return response
        new_post_edit_form = PostEditForm(request=request)
        await new_post_edit_form.load_data()
        if await new_post_edit_form.is_valid(session):
            await CRUD.modify_post(
                post_id=new_post_edit_form.post_id,
                session=session,
                values={
                    'topic': new_post_edit_form.topic,
                    'text': new_post_edit_form.text,
                    'category': new_post_edit_form.category,
                    'modified': True,
                }
            )
        else:

            new_post_edit_form.__dict__['user'] = user

            return templates.TemplateResponse('edit_post.html', context=new_post_edit_form.__dict__)

        redirect_url = request.url_for('index')
        response = RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER)
        return response


@web_router.get("/view-my-posts")
async def view_my_posts(request: Request, add_comment=Form(None), post_id=Form(None), search: str = Form(None),
                        user=Depends(SecurityHandler.get_current_user_web),
                        session: AsyncSession = Depends(get_async_session)):
    posts = await CRUD.get_posts_by_user_id(session, q=search, user_id=user.id)
    items = []
    for post in posts:
        post_user = await CRUD.get_user_by_id(user_id=post.user_id, session=session)
        comments = await CRUD.fetch_comments_by_post_id(session=session, post_id=post.id)
        num_of_comments = len(comments)
        comment_users = []
        for comment in comments:
            comment_user = await CRUD.get_user_by_id(user_id=comment.user_id, session=session)
            comment_users.append(comment_user)
        item = [post, post_user, num_of_comments, comments, comment_users]
        items.append(item)
    context = {
        'request': request,
        'user': user,
        'items': items,
    }

    if add_comment and post_id:
        await CRUD.create_comment(
            session=session,
            text=add_comment,
            user_id=user.id,
            post_id=int(post_id)
        )

        items = []
        for post in posts:
            post_user = await CRUD.get_user_by_id(user_id=post.user_id, session=session)
            comments = await CRUD.fetch_comments_by_post_id(session=session, post_id=post.id)
            num_of_comments = len(comments)
            comment_users = []
            for comment in comments:
                comment_user = await CRUD.get_user_by_id(user_id=comment.user_id, session=session)
                comment_users.append(comment_user)
            item = [post, post_user, num_of_comments, comments, comment_users]
            items.append(item)
        context = {
            'request': request,
            'user': user,
            'items': items,
        }

    return templates.TemplateResponse('index.html', context=context)


@web_router.get("/view-my-account")
async def view_my_account(request: Request, user=Depends(SecurityHandler.get_current_user_web)):
    context = {
        'request': request,
        'user': user,
    }

    return templates.TemplateResponse('view_profile.html', context=context)


@web_router.get("/edit-profile")
@web_router.post("/edit-profile")
async def edit_profile(request: Request, background_tasks: BackgroundTasks,
                       user=Depends(SecurityHandler.get_current_user_web),
                       session: AsyncSession = Depends(get_async_session), ):

    content = {
        'request': request,
        'user': user,
    }

    if not user:
        response = templates.TemplateResponse('login.html', context=content)
        return response

    if request.method == 'GET':
        response = templates.TemplateResponse('edit_profile.html', context=content)
        return response

    edit_user_form = UserUpdateForm(request=request, user=user)
    await edit_user_form.load_data()
    if await edit_user_form.is_valid(session):
        if edit_user_form.new_email != edit_user_form.initial_email:
            await CRUD.modify_user(user_id=user.id,
                                   session=session,
                                   values={
                                       'email': edit_user_form.new_email,
                                       'name': edit_user_form.new_name,
                                       'verified': False,
                                       'image_url': edit_user_form.new_image_url,
                                       'image_file': edit_user_form.new_image_file_name
                                   })

            background_tasks.add_task(
                send_email_verification,
                user_email=edit_user_form.new_email,
                user_uuid=user.user_uuid,
                user_name=edit_user_form.new_name,
                host=request.base_url,
                is_web=True
            )
        else:
            await CRUD.modify_user(session=session,
                                   user_id=user.id,
                                   values={
                                       'name': edit_user_form.new_name,
                                       'image_url': edit_user_form.new_image_url,
                                       'image_file': edit_user_form.new_image_file_name
                                   })

        redirect_url = request.url_for('index')
        response = RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER)
        return await SecurityHandler.set_cookies_web(user, response)
    else:
        return templates.TemplateResponse('edit_profile.html', context=edit_user_form.__dict__)


@web_router.get('/change_password')
async def change_password_get(request: Request, user=Depends(SecurityHandler.get_current_user_web)):
    return templates.TemplateResponse('change_password.html', context={'request': request, 'user': user})


@web_router.post('/change_password')
async def change_password_post(request: Request, user=Depends(SecurityHandler.get_current_user_web),
                               current_password: str = Form(),
                               new_password: str = Form(),
                               new_password_confirm: str = Form(),
                               session: AsyncSession = Depends(get_async_session)):

    errors = []
    is_current_password_correct = await PasswordEncrypt.verify_password(plain_password=current_password,
                                                                        hashed_password=user.hashed_password)
    if not is_current_password_correct:
        errors.append('Current password is incorrect')

    if len(new_password) < 8:
        errors.append('New password must be at least 8 symbols')

    if new_password != new_password_confirm:
        errors.append("New password and its confirmation aren't matching")

    if errors:
        return templates.TemplateResponse('change_password.html',
                                          context={'request': request, 'errors': errors, 'user': user})

    else:
        new_hashed_password = await PasswordEncrypt.get_password_hash(password=new_password)
        await CRUD.modify_user(session=session, user_id=user.id, values={'hashed_password': new_hashed_password})
        redirect_url = request.url_for('index')
        response = RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER)
        return await SecurityHandler.set_cookies_web(user, response)


@web_router.get('/your_account_was_verified')
async def get_verification(request: Request,
                           user=Depends(SecurityHandler.get_current_user_web),
                           session: AsyncSession = Depends(get_async_session)):
    await CRUD.verify_user_account(user_uuid=user.user_uuid, session=session)
    return templates.TemplateResponse('get_verification.html', context={'request': request, 'user': user})


@web_router.get("/")
@web_router.get("/page={page}")
@web_router.post("/")
async def index(request: Request, search: str = Form(None), page: int = None,
                add_comment=Form(None), post_id=Form(None),
                user=Depends(SecurityHandler.get_current_user_web),
                session: AsyncSession = Depends(get_async_session)):
    if page:
        posts = await CRUD.fetch_posts(session, q=search, offset=12*(page-1))
    else:
        posts = await CRUD.fetch_posts(session, q=search)
    items = []
    for post in posts:
        post_user = await CRUD.get_user_by_id(user_id=post.user_id, session=session)
        comments = await CRUD.fetch_comments_by_post_id(session=session, post_id=post.id)
        num_of_comments = len(comments)
        comment_users = []
        for comment in comments:
            comment_user = await CRUD.get_user_by_id(user_id=comment.user_id, session=session)
            comment_users.append(comment_user)
        item = [post, post_user, num_of_comments, comments, comment_users]
        items.append(item)
    context = {
        'request': request,
        'user': user,
        'items': items,
    }

    if add_comment and post_id:
        await CRUD.create_comment(
            session=session,
            text=add_comment,
            user_id=user.id,
            post_id=int(post_id)
        )

        items = []
        for post in posts:
            post_user = await CRUD.get_user_by_id(user_id=post.user_id, session=session)
            comments = await CRUD.fetch_comments_by_post_id(session=session, post_id=post.id)
            num_of_comments = len(comments)
            comment_users = []
            for comment in comments:
                comment_user = await CRUD.get_user_by_id(user_id=comment.user_id, session=session)
                comment_users.append(comment_user)
            item = [post, post_user, num_of_comments, comments, comment_users]
            items.append(item)
        context = {
            'request': request,
            'user': user,
            'items': items,
        }

    return templates.TemplateResponse('index.html', context=context)
