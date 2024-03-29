"""remuved_nickname

Revision ID: dde4b9166e87
Revises: 39e5d4490f4f
Create Date: 2024-03-12 22:13:54.304863

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dde4b9166e87'
down_revision: Union[str, None] = '39e5d4490f4f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint(None, 'users', ['name'])
    op.drop_column('users', 'nickname')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('nickname', sa.VARCHAR(length=20), autoincrement=False, nullable=False))
    op.drop_constraint(None, 'users', type_='unique')
    # ### end Alembic commands ###
