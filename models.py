from datetime import datetime
from typing import Optional
import uuid
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.orm import mapped_column

from database import Base

default_user_image_url = 'https://www.tenforums.com/attachments/user-accounts-family-safety/322690d1615743307t-user-account-image-log-user.png?s=c6ec74e460c755546f9c3ef47b6d6645'


class BaseInfoMixin:
    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class User(BaseInfoMixin, Base):
    __tablename__ = "users"

    name: Mapped[str] = mapped_column(String(50), unique=True)
    email: Mapped[str] = mapped_column(unique=True, index=True)
    hashed_password: Mapped[str]
    user_uuid: Mapped[uuid.UUID] = mapped_column(default=uuid.uuid4)
    is_admin: Mapped[bool] = mapped_column(default=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    verified: Mapped[bool] = mapped_column(default=False)
    image_url: Mapped[str] = mapped_column(default=default_user_image_url, nullable=False)
    image_file: Mapped[str] = mapped_column(default='', nullable=False)

    tokens = relationship('UserRefreshToken', back_populates='user_for_token')
    post = relationship('Post', back_populates='user_for_post')
    comment_for_user = relationship('Comment', back_populates='user_for_comment')


class UserRefreshToken(BaseInfoMixin, Base):
    __tablename__ = 'refresh_tokens'

    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    refresh_key: Mapped[str]
    expires_at: Mapped[datetime]

    user_for_token = relationship('User', back_populates='tokens')


class Post(BaseInfoMixin, Base):
    __tablename__ = 'posts'

    topic: Mapped[str] = mapped_column(String(50))
    text: Mapped[str] = mapped_column(String(500))
    category: Mapped[str] = mapped_column(String(25))
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    modified: Mapped[bool] = mapped_column(default=False)

    user_for_post = relationship('User', back_populates='post')
    comment = relationship('Comment', back_populates='post_for_comment')


class Comment(BaseInfoMixin, Base):
    __tablename__ = 'comments'

    text: Mapped[str] = mapped_column(String(100))
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    post_id: Mapped[int] = mapped_column(ForeignKey('posts.id'))

    user_for_comment = relationship('User', back_populates='comment_for_user')
    post_for_comment = relationship('Post', back_populates='comment')
