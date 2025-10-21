"""Auto-generated Alembic migration script."""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '580b047cd286'
down_revision = '307c578ee48f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add created_at and updated_at columns with server defaults for compatibility
    # Use server_default CURRENT_TIMESTAMP so existing rows are populated on apply
    op.add_column(
        'events',
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.add_column(
        'events',
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )


def downgrade() -> None:
    # Remove the timestamp columns
    op.drop_column('events', 'updated_at')
    op.drop_column('events', 'created_at')
