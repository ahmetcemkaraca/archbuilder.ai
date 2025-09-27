from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0001_init'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('email', sa.String(length=256), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(length=256), nullable=False),
        sa.Column('role', sa.String(length=32), nullable=False),
        sa.Column(
            'is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')
        ),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_role', 'users', ['role'])

    op.create_table(
        'projects',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column(
            'owner_id',
            sa.String(length=36),
            sa.ForeignKey('users.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_projects_owner_id', 'projects', ['owner_id'])
    op.create_index('ix_projects_name', 'projects', ['name'])

    op.create_table(
        'ai_commands',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column(
            'user_id',
            sa.String(length=36),
            sa.ForeignKey('users.id', ondelete='SET NULL'),
            nullable=True,
        ),
        sa.Column(
            'project_id',
            sa.String(length=36),
            sa.ForeignKey('projects.id', ondelete='SET NULL'),
            nullable=True,
        ),
        sa.Column('command', sa.String(length=100), nullable=False),
        sa.Column('input', sa.JSON(), nullable=False),
        sa.Column('output', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_ai_commands_user_id', 'ai_commands', ['user_id'])
    op.create_index('ix_ai_commands_project_id', 'ai_commands', ['project_id'])

    op.create_table(
        'subscriptions',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column(
            'user_id',
            sa.String(length=36),
            sa.ForeignKey('users.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column('plan', sa.String(length=50), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('ends_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_subscriptions_user_id', 'subscriptions', ['user_id'])

    op.create_table(
        'usage',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column(
            'user_id',
            sa.String(length=36),
            sa.ForeignKey('users.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column('usage_type', sa.String(length=50), nullable=False),
        sa.Column('units', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_usage_user_id', 'usage', ['user_id'])
    op.create_index('ix_usage_usage_type', 'usage', ['usage_type'])
    op.create_index('ix_usage_date', 'usage', ['date'])


def downgrade() -> None:
    op.drop_index('ix_usage_date', table_name='usage')
    op.drop_index('ix_usage_usage_type', table_name='usage')
    op.drop_index('ix_usage_user_id', table_name='usage')
    op.drop_table('usage')

    op.drop_index('ix_subscriptions_user_id', table_name='subscriptions')
    op.drop_table('subscriptions')

    op.drop_index('ix_ai_commands_project_id', table_name='ai_commands')
    op.drop_index('ix_ai_commands_user_id', table_name='ai_commands')
    op.drop_table('ai_commands')

    op.drop_index('ix_projects_name', table_name='projects')
    op.drop_index('ix_projects_owner_id', table_name='projects')
    op.drop_table('projects')

    op.drop_index('ix_users_role', table_name='users')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
