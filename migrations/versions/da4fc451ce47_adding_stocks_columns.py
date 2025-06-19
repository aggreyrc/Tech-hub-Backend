"""Adding stocks columns

Revision ID: da4fc451ce47
Revises: 35f00d9fcdac
Create Date: 2025-06-19 18:46:56.784382

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'da4fc451ce47'
down_revision = '35f00d9fcdac'
branch_labels = None
depends_on = None


def upgrade():
    # Add the column as nullable first
    op.add_column('products', sa.Column('amount_in_stock', sa.Integer(), nullable=True))
    # Set default value for existing rows
    op.execute('UPDATE products SET amount_in_stock = 0 WHERE amount_in_stock IS NULL')
    # Alter column to NOT NULL
    op.alter_column('products', 'amount_in_stock', nullable=False)
    # Optionally, set a default for future inserts
    op.alter_column('products', 'amount_in_stock', server_default='0')

def downgrade():
    op.drop_column('products', 'amount_in_stock')

    # ### end Alembic commands ###
