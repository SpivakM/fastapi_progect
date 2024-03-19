from sqlalchemy import insert, select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from models import User, UserRefreshToken, Post, Comment
from database import async_session_maker

from datetime import datetime


# ---------- USERS -------------


async def create_user(
        name: str,
        email: str,
        hashed_password: str,
        image_url: str,
        image_file: str,
        session: AsyncSession,
) -> User:
    user = User(
        email=email,
        name=name,
        hashed_password=hashed_password,
        image_file=image_file,
        image_url=image_url
    )
    session.add(user)
    try:
        await session.commit()
        await session.refresh(user)
        return user
    except IntegrityError:
        await session.rollback()
        raise HTTPException(detail=f'User with email {email} already exists', status_code=status.HTTP_403_FORBIDDEN)


async def get_user_by_email(user_email: str, session: AsyncSession) -> User | None:
    query = select(User).filter_by(email=user_email)
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def get_user_by_name(user_name: str, session: AsyncSession) -> User | None:
    query = select(User).filter_by(name=user_name)
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def get_user_by_uuid(user_uuid: str, session: AsyncSession) -> User | None:
    query = select(User).filter_by(user_uuid=user_uuid)
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def verify_user_account(user_uuid: str, session: AsyncSession) -> User | None:
    user = await get_user_by_uuid(user_uuid, session)
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Data for account activation is not correct")
    if user.verified:
        return user

    user.verified = True
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def modify_user(session: AsyncSession, user_id, values: dict):
    query = update(User).where(User.id == user_id).values(**values)
    await session.execute(query)
    await session.commit()


async def fetch_users(skip: int = 0, limit: int = 10) -> list[User]:
    async with async_session_maker() as session:
        query = select(User).offset(skip).limit(limit)
        result = await session.execute(query)
        print(query)
        # print(type(result.scalars().all()))
        print(result.scalars().all()[0].login)
        # print(result.scalars().all()[0].__dict__)
        return result.scalars().all()


async def get_user_by_id(user_id: int, session: AsyncSession) -> User | None:
    query = select(User).filter_by(id=user_id)
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def update_user(user_id: int, values: dict):
    if not values:
        return
    async with async_session_maker() as session:
        query = update(User).where(User.id == user_id).values(**values)
        await session.execute(query)
        await session.commit()
        # print(tuple(result))
        print(query)


async def delete_user(user_id: int):
    async with async_session_maker() as session:
        query = delete(User).where(User.id == user_id)
        await session.execute(query)
        await session.commit()
        print(query)


async def create_refresh_token(
        user_id: int,
        refresh_key: str,
        expires_at: datetime,
        session: AsyncSession,
) -> None:
    token = UserRefreshToken(
        user_id=user_id,
        refresh_key=refresh_key,
        expires_at=expires_at,
    )
    session.add(token)
    await session.commit()


async def get_refresh_token_by_key(key: str, session: AsyncSession) -> UserRefreshToken | None:
    user_token = await session.execute(
        select(UserRefreshToken)
        .options(joinedload(UserRefreshToken.user_id))
        .where(
            UserRefreshToken.refresh_key == key,
            UserRefreshToken.expires_at > datetime.utcnow(),
        )
    )

    return user_token.scalar_one_or_none()


# ----------- POSTS ------------

async def create_post(session: AsyncSession,
                      topic: str,
                      text: str,
                      category: str,
                      user_id: int) -> None:
    post = Post(
        topic=topic,
        text=text,
        category=category,
        user_id=user_id
    )
    session.add(post)
    await session.commit()
    await session.refresh(post)


async def fetch_posts(session: AsyncSession, limit: int = 12, offset=0, q='') -> list:
    if q:
        query = select(Post).filter(Post.category.ilike(f'%{q}%')).offset(offset).limit(limit).order_by(Post.id)
    else:
        query = select(Post).offset(offset).limit(limit).order_by(Post.id)
    result = await session.execute(query)
    return result.scalars().all() or []


async def get_posts_by_user_id(session: AsyncSession, limit: int = 12, offset=0, user_id='', q='') -> list:
    if q:
        query = select(Post).where(Post.user_id == user_id).filter(Post.category.ilike(f'%{q}%')).offset(offset).limit(
            limit).order_by(Post.id)
    else:
        query = select(Post).where(Post.user_id == user_id).offset(offset).limit(limit).order_by(Post.id)
    result = await session.execute(query)
    return result.scalars().all() or []


async def modify_post(session: AsyncSession, post_id, values: dict):
    query = update(Post).where(Post.id == post_id).values(**values)
    await session.execute(query)
    await session.commit()


async def get_post_by_id(post_id: int, session: AsyncSession) -> Post | None:
    query = select(Post).filter_by(id=post_id)
    result = await session.execute(query)
    return result.scalar_one_or_none()


# ----------- COMMENTS ---------------


async def create_comment(session: AsyncSession,
                         text: str,
                         user_id: int,
                         post_id: int) -> None:
    comment = Comment(
        text=text,
        user_id=user_id,
        post_id=post_id
    )
    session.add(comment)
    await session.commit()
    await session.refresh(comment)


async def fetch_comments_by_post_id(session: AsyncSession, post_id: int) -> list:
    query = select(Comment).where(Comment.post_id == post_id)
    result = await session.execute(query)
    return result.scalars().all() or []
