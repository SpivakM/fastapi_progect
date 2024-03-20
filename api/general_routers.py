from fastapi import APIRouter, Depends, Request, HTTPException, status
from library.security_lib import SecurityHandler
from sqlalchemy.ext.asyncio import AsyncSession
import CRUD
from database import get_async_session

router_public = APIRouter(
    prefix='/api/public',
    tags=['API', 'Posts', 'Public']
)


router_private = APIRouter(
    prefix='/api/private',
    tags=['API', 'Posts', 'Private'],
    dependencies=[Depends(SecurityHandler.oauth2_scheme), Depends(SecurityHandler.get_current_user)]
)


@router_public.get('/view_posts')
async def get_posts(search: str = '', session: AsyncSession = Depends(get_async_session),
                    limit: int = 12, offset: int = 0):
    posts = await CRUD.fetch_posts(session=session, q=search, limit=limit, offset=offset)
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
        items.append({post.id: item})
    return items


@router_private.post('/create_post/')
async def create_post_api(request: Request, topic: str, text: str, category: str,
                          session: AsyncSession = Depends(get_async_session)):
    token = str(request.headers.__dict__['_list'][7][1].decode('UTF-8').split(' ')[1])
    user = await SecurityHandler.get_current_user(token=token, session=session)
    if not user:
        raise HTTPException(detail='Must be signed up to create post',
                            status_code=status.HTTP_401_UNAUTHORIZED)

    if not topic:
        raise HTTPException(detail='Write a topic',
                            status_code=status.HTTP_400_BAD_REQUEST)

    if not text:
        raise HTTPException(detail='Write a text',
                            status_code=status.HTTP_400_BAD_REQUEST)

    if not category:
        raise HTTPException(detail='Write a category',
                            status_code=status.HTTP_400_BAD_REQUEST)

    if len(topic) > 50:
        raise HTTPException(detail='Topic must be less than 50 symbols',
                            status_code=status.HTTP_400_BAD_REQUEST)

    if len(text) > 500:
        raise HTTPException(detail='Text must be less than 500 symbols',
                            status_code=status.HTTP_400_BAD_REQUEST)

    if len(category) > 25:
        raise HTTPException(detail='Text must be less than 25 symbols',
                            status_code=status.HTTP_400_BAD_REQUEST)

    post = await CRUD.create_post(session=session, topic=topic, text=text, category=category, user_id=user.id)
    return post


@router_private.post('/create_comment/')
async def create_post_api(request: Request, text: str, post_id: int,
                          session: AsyncSession = Depends(get_async_session)):
    token = str(request.headers.__dict__['_list'][7][1].decode('UTF-8').split(' ')[1])
    user = await SecurityHandler.get_current_user(token=token, session=session)
    if not user:
        raise HTTPException(detail='Must be signed up to create post',
                            status_code=status.HTTP_401_UNAUTHORIZED)

    if not text:
        raise HTTPException(detail='Write a text',
                            status_code=status.HTTP_400_BAD_REQUEST)

    if len(text) > 100:
        raise HTTPException(detail='Text must be less than 100 symbols',
                            status_code=status.HTTP_400_BAD_REQUEST)

    if not post_id:
        raise HTTPException(detail='Must be post id',
                            status_code=status.HTTP_400_BAD_REQUEST)

    if not await CRUD.get_post_by_id(post_id=post_id, session=session):
        raise HTTPException(detail='Must be a valid post id',
                            status_code=status.HTTP_400_BAD_REQUEST)

    comment = await CRUD.create_comment(session=session, text=text, user_id=user.id, post_id=post_id)
    return comment
