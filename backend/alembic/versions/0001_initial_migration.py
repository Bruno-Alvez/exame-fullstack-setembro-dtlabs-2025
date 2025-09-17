"""Initial migration

Revision ID: 0001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    
    # Create devices table
    op.create_table('devices',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('location', sa.String(length=255), nullable=False),
        sa.Column('serial_number', sa.String(length=12), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('last_seen', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('serial_number')
    )
    
    # Create heartbeats table
    op.create_table('heartbeats',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('device_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('cpu_usage', sa.Float(), nullable=False),
        sa.Column('ram_usage', sa.Float(), nullable=False),
        sa.Column('temperature', sa.Float(), nullable=False),
        sa.Column('free_disk_space', sa.Float(), nullable=False),
        sa.Column('dns_latency', sa.Float(), nullable=False),
        sa.Column('connectivity', sa.Boolean(), nullable=False),
        sa.Column('boot_timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('health_score', sa.Float(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create alerts table
    op.create_table('alerts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('device_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('conditions', sa.JSON(), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=False, default=5),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('last_triggered', sa.DateTime(timezone=True), nullable=True),
        sa.Column('trigger_count', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for better performance
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_devices_user_id', 'devices', ['user_id'])
    op.create_index('ix_devices_serial_number', 'devices', ['serial_number'], unique=True)
    op.create_index('ix_heartbeats_device_id', 'heartbeats', ['device_id'])
    op.create_index('ix_heartbeats_timestamp', 'heartbeats', ['timestamp'])
    op.create_index('ix_alerts_device_id', 'alerts', ['device_id'])
    op.create_index('ix_alerts_is_active', 'alerts', ['is_active'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_alerts_is_active', table_name='alerts')
    op.drop_index('ix_alerts_device_id', table_name='alerts')
    op.drop_index('ix_heartbeats_timestamp', table_name='heartbeats')
    op.drop_index('ix_heartbeats_device_id', table_name='heartbeats')
    op.drop_index('ix_devices_serial_number', table_name='devices')
    op.drop_index('ix_devices_user_id', table_name='devices')
    op.drop_index('ix_users_email', table_name='users')
    
    # Drop tables
    op.drop_table('alerts')
    op.drop_table('heartbeats')
    op.drop_table('devices')
    op.drop_table('users')
