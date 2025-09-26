"""Enhanced authentication models migration

Revision ID: 002_enhanced_auth
Revises: 001_initial_schema
Create Date: 2025-09-26 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '002_enhanced_auth'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enhanced user table with new fields
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS first_name VARCHAR(128)")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_name VARCHAR(128)")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT FALSE")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_locked BOOLEAN DEFAULT FALSE")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(36)")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS organization_name VARCHAR(256)")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login TIMESTAMP")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS login_attempts INTEGER DEFAULT 0")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS lockout_until TIMESTAMP")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS password_changed_at TIMESTAMP DEFAULT NOW()")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW()")
    
    # Update role column to use enum
    op.execute("ALTER TABLE users ALTER COLUMN role TYPE VARCHAR(32)")
    
    # Create indexes
    op.execute("CREATE INDEX IF NOT EXISTS idx_users_tenant_id ON users(tenant_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active)")
    
    # Create api_keys table
    op.create_table('api_keys',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('key_hash', sa.String(256), unique=True, index=True, nullable=False),
        sa.Column('key_prefix', sa.String(16), index=True, nullable=False),
        sa.Column('name', sa.String(128), nullable=False),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), index=True, nullable=False),
        sa.Column('status', sa.String(32), default='active', index=True, nullable=False),
        sa.Column('permissions', sa.Text, nullable=True),
        sa.Column('usage_count', sa.Integer, default=0, nullable=False),
        sa.Column('last_used', sa.DateTime, nullable=True),
        sa.Column('expires_at', sa.DateTime, nullable=True, index=True),
        sa.Column('rate_limit_per_hour', sa.Integer, nullable=True),
        sa.Column('rate_limit_per_day', sa.Integer, nullable=True),
        sa.Column('allowed_ips', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now(), index=True, nullable=False),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('revoked_at', sa.DateTime, nullable=True)
    )
    
    # Create user_sessions table
    op.create_table('user_sessions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), index=True, nullable=False),
        sa.Column('status', sa.String(32), default='active', index=True, nullable=False),
        sa.Column('device_info', sa.Text, nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=False),
        sa.Column('user_agent', sa.Text, nullable=True),
        sa.Column('location', sa.String(256), nullable=True),
        sa.Column('expires_at', sa.DateTime, index=True, nullable=False),
        sa.Column('last_activity', sa.DateTime, default=sa.func.now(), nullable=False),
        sa.Column('created_at', sa.DateTime, default=sa.func.now(), index=True, nullable=False),
        sa.Column('ended_at', sa.DateTime, nullable=True)
    )
    
    # Create refresh_tokens table
    op.create_table('refresh_tokens',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('token_hash', sa.String(256), unique=True, index=True, nullable=False),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), index=True, nullable=False),
        sa.Column('session_id', sa.String(36), sa.ForeignKey('user_sessions.id'), nullable=True),
        sa.Column('expires_at', sa.DateTime, index=True, nullable=False),
        sa.Column('is_revoked', sa.Boolean, default=False, index=True, nullable=False),
        sa.Column('issued_ip', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now(), index=True, nullable=False),
        sa.Column('used_at', sa.DateTime, nullable=True),
        sa.Column('revoked_at', sa.DateTime, nullable=True)
    )
    
    # Create audit_logs table
    op.create_table('audit_logs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=True, index=True),
        sa.Column('event_type', sa.String(128), index=True, nullable=False),
        sa.Column('resource', sa.String(256), nullable=True),
        sa.Column('action', sa.String(128), nullable=False),
        sa.Column('outcome', sa.String(32), index=True, nullable=False),
        sa.Column('ip_address', sa.String(45), index=True, nullable=False),
        sa.Column('user_agent', sa.Text, nullable=True),
        sa.Column('correlation_id', sa.String(64), nullable=True, index=True),
        sa.Column('details', sa.Text, nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('tenant_id', sa.String(36), nullable=True, index=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now(), index=True, nullable=False)
    )


def downgrade() -> None:
    # Drop new tables
    op.drop_table('audit_logs')
    op.drop_table('refresh_tokens')
    op.drop_table('user_sessions')
    op.drop_table('api_keys')
    
    # Remove new columns from users table
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS first_name")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS last_name")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS is_verified")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS is_locked")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS tenant_id")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS organization_name")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS last_login")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS login_attempts")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS lockout_until")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS password_changed_at")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS updated_at")
    
    # Drop indexes
    op.execute("DROP INDEX IF EXISTS idx_users_tenant_id")
    op.execute("DROP INDEX IF EXISTS idx_users_created_at")
    op.execute("DROP INDEX IF EXISTS idx_users_is_active")