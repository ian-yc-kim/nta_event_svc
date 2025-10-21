"""Auto-generated Alembic migration script."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '307c578ee48f'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Determine dialect to choose a compatible participants type
    bind = op.get_bind()
    dialect = getattr(bind, 'dialect', None)
    dialect_name = dialect.name if dialect is not None else None

    if dialect_name == 'postgresql':
        participants_type = postgresql.ARRAY(sa.String())
    else:
        # Use JSON on sqlite and other dialects for compatibility
        participants_type = sa.JSON()

    op.create_table(
        'events',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('start_time', sa.DateTime(), nullable=True),
        sa.Column('end_time', sa.DateTime(), nullable=True),
        sa.Column('location', sa.String(), nullable=True),
        sa.Column('participants', participants_type, nullable=True),
    )


def downgrade() -> None:
    op.drop_table('events')
