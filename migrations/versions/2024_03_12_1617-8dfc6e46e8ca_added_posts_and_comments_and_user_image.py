"""added_posts_and_comments_and_user_image

Revision ID: 8dfc6e46e8ca
Revises: 7626b8f8201e
Create Date: 2024-03-12 16:17:36.966194

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8dfc6e46e8ca'
down_revision: Union[str, None] = '7626b8f8201e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('posts',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('topic', sa.String(length=50), nullable=False),
    sa.Column('text', sa.String(length=500), nullable=False),
    sa.Column('category', sa.String(length=25), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('modified', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('comments',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('text', sa.String(length=100), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('post_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['post_id'], ['posts.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.add_column('users', sa.Column('image_url', sa.String(), nullable=True))
    op.add_column('users', sa.Column('image_file', sa.String(), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'image_file')
    op.drop_column('users', 'image_url')
    op.drop_table('comments')
    op.drop_table('posts')
    # ### end Alembic commands ###
