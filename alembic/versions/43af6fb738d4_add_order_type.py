from alembic import op
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as pg

# revision identifiers
revision = '43af6fb738d4'
down_revision = 'dfdfb0a1c4ea'
branch_labels = None
depends_on = None


# Define the new PostgreSQL ENUM type
order_type_enum = pg.ENUM(
    'loading', 'unloading', 'place_changing',
    name='ordertype', create_type=False  # `create_type=False` avoids conflicts
)


def upgrade():
    # Create the enum type in the DB
    order_type_enum.create(op.get_bind(), checkfirst=True)

    # Add the column using the new ENUM type
    op.add_column('orders', sa.Column('order_type', order_type_enum, nullable=False))


def downgrade():
    op.drop_column('orders', 'order_type')
    order_type_enum.drop(op.get_bind(), checkfirst=True)
