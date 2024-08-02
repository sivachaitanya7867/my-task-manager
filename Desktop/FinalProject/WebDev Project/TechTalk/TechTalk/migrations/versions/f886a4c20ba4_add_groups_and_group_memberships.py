"""Add groups and group memberships

Revision ID: f886a4c20ba4
Revises: aa1231427023
Create Date: 2024-08-01 12:09:40.690512

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f886a4c20ba4'
down_revision = 'aa1231427023'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('post', schema=None) as batch_op:
        batch_op.drop_index('ix_post_group_id')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('post', schema=None) as batch_op:
        batch_op.create_index('ix_post_group_id', ['group_id'], unique=False)

    # ### end Alembic commands ###
