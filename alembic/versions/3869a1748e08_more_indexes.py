"""More indexes

Revision ID: 3869a1748e08
Revises: 40b065559e29
Create Date: 2014-11-04 13:45:53.639100

"""

# revision identifiers, used by Alembic.
revision = '3869a1748e08'
down_revision = '40b065559e29'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_index(u'ix_resolution_result_package_id', 'resolution_result', ['package_id'], unique=False)
    op.create_index(u'ix_resolution_result_element_resolution_id', 'resolution_result_element', ['resolution_id'], unique=False)
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(u'ix_resolution_result_element_resolution_id', table_name='resolution_result_element')
    op.drop_index(u'ix_resolution_result_package_id', table_name='resolution_result')
    ### end Alembic commands ###
