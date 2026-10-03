"""Initial Schema for Incidents, Events, Deployments, Code Reviews, Actions, Memories, and Audits

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-03 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Services
    op.create_table(
        'services',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('name', sa.String(length=128), nullable=False, unique=True),
        sa.Column('environment', sa.String(length=64), nullable=False, server_default='production'),
        sa.Column('description', sa.Text(), nullable=False, server_default=''),
        sa.Column('dependencies', sa.JSON(), nullable=False),
        sa.Column('metadata_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_services_name', 'services', ['name'], unique=True)

    # Incidents
    op.create_table(
        'incidents',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('title', sa.String(length=256), nullable=False),
        sa.Column('severity', sa.String(length=32), nullable=False, server_default='MEDIUM'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='DETECTED'),
        sa.Column('service_id', sa.String(length=64), sa.ForeignKey('services.id'), nullable=False),
        sa.Column('environment', sa.String(length=64), nullable=False, server_default='production'),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('root_cause', sa.Text(), nullable=True),
        sa.Column('confidence', sa.String(length=32), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('idx_incident_status_severity', 'incidents', ['status', 'severity'])

    # Events
    op.create_table(
        'events',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('source', sa.String(length=128), nullable=False, server_default='runtime'),
        sa.Column('service', sa.String(length=128), nullable=False),
        sa.Column('environment', sa.String(length=64), nullable=False, server_default='production'),
        sa.Column('level', sa.String(length=32), nullable=False, server_default='INFO'),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('event_type', sa.String(length=64), nullable=False, server_default='error_log'),
        sa.Column('signature', sa.String(length=128), nullable=False),
        sa.Column('metadata_json', sa.JSON(), nullable=False),
        sa.Column('incident_id', sa.String(length=64), sa.ForeignKey('incidents.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('idx_event_service_type_time', 'events', ['service', 'event_type', 'timestamp'])

    # Deployments
    op.create_table(
        'deployments',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('version', sa.String(length=64), nullable=False),
        sa.Column('commit_hash', sa.String(length=64), nullable=False),
        sa.Column('environment', sa.String(length=64), nullable=False, server_default='production'),
        sa.Column('service', sa.String(length=128), nullable=False),
        sa.Column('deployed_at', sa.DateTime(), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='SUCCESS'),
        sa.Column('metadata_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('idx_deployment_service_time', 'deployments', ['service', 'deployed_at'])

    # Code Reviews
    op.create_table(
        'code_reviews',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('commit_hash', sa.String(length=64), nullable=False),
        sa.Column('tool', sa.String(length=64), nullable=False, server_default='CodeGuard'),
        sa.Column('finding', sa.Text(), nullable=False),
        sa.Column('severity', sa.String(length=32), nullable=False, server_default='MEDIUM'),
        sa.Column('file', sa.String(length=256), nullable=False),
        sa.Column('line', sa.Integer(), nullable=True),
        sa.Column('decision', sa.String(length=32), nullable=False, server_default='PASS'),
        sa.Column('metadata_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('idx_codereview_commit_decision', 'code_reviews', ['commit_hash', 'decision'])

    # Actions
    op.create_table(
        'actions',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('incident_id', sa.String(length=64), sa.ForeignKey('incidents.id'), nullable=False),
        sa.Column('type', sa.String(length=64), nullable=False),
        sa.Column('risk_level', sa.String(length=32), nullable=False, server_default='MEDIUM'),
        sa.Column('proposed_by', sa.String(length=128), nullable=False, server_default='ResponsePlannerAgent'),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('expected_impact', sa.Text(), nullable=False),
        sa.Column('rollback_path', sa.Text(), nullable=False, server_default=''),
        sa.Column('approval_status', sa.String(length=32), nullable=False, server_default='PENDING'),
        sa.Column('approved_by', sa.String(length=128), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('executed_at', sa.DateTime(), nullable=True),
        sa.Column('result_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('idx_action_incident_status', 'actions', ['incident_id', 'approval_status'])

    # Incident Memories
    op.create_table(
        'incident_memories',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('incident_id', sa.String(length=64), sa.ForeignKey('incidents.id'), nullable=False, unique=True),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('symptoms', sa.Text(), nullable=False),
        sa.Column('rca', sa.Text(), nullable=False),
        sa.Column('resolution', sa.Text(), nullable=False),
        sa.Column('outcome', sa.Text(), nullable=False),
        sa.Column('embedding', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    # Audit Logs
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('actor', sa.String(length=128), nullable=False),
        sa.Column('action', sa.String(length=128), nullable=False),
        sa.Column('target', sa.String(length=256), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False, server_default=''),
        sa.Column('result', sa.String(length=64), nullable=False, server_default='SUCCESS'),
        sa.Column('metadata_json', sa.JSON(), nullable=False),
    )
    op.create_index('idx_audit_actor_action_time', 'audit_logs', ['actor', 'action', 'timestamp'])


def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('incident_memories')
    op.drop_table('actions')
    op.drop_table('code_reviews')
    op.drop_table('deployments')
    op.drop_table('events')
    op.drop_table('incidents')
    op.drop_table('services')
