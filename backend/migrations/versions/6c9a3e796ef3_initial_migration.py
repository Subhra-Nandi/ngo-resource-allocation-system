"""initial migration

Revision ID: 6c9a3e796ef3
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

import geoalchemy2
import sqlalchemy as sa
from alembic import op

revision: str = '6c9a3e796ef3'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'ngo_users',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True),
        sa.Column('ngo_name', sa.String(200), nullable=False),
        sa.Column('email', sa.String(200), nullable=False, unique=True),
        sa.Column('hashed_password', sa.String(200), nullable=False),
        sa.Column('contact_phone', sa.String(20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        'ngo_resources',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True),
        sa.Column('ngo_id', sa.UUID(as_uuid=True), sa.ForeignKey('ngo_users.id'), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('name', sa.Text, nullable=False),
        sa.Column('quantity', sa.Integer, nullable=False, default=0),
        sa.Column('unit', sa.String(30), nullable=True),
        sa.Column('depot_location', geoalchemy2.types.Geometry(geometry_type='POINT', srid=4326), nullable=False),
        sa.Column('depot_address', sa.Text, nullable=True),
        sa.Column('depot_name', sa.String(200), nullable=True),
        sa.Column('expiry_date', sa.Date, nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        'user_reports',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True),
        sa.Column('source', sa.String(30), nullable=False),
        sa.Column('user_gps', geoalchemy2.types.Geometry(geometry_type='POINT', srid=4326), nullable=True),
        sa.Column('user_address', sa.Text, nullable=True),
        sa.Column('location_name', sa.String(300), nullable=True),
        sa.Column('need_type', sa.String(50), nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('severity', sa.Integer, nullable=True),
        sa.Column('affected_count', sa.Integer, nullable=True),
        sa.Column('status', sa.String(30), nullable=False),
        sa.Column('ai_confidence', sa.Float, nullable=True),
        sa.Column('ai_flag_reason', sa.Text, nullable=True),
        sa.Column('matched_ngo_id', sa.UUID(as_uuid=True), sa.ForeignKey('ngo_users.id'), nullable=True),
        sa.Column('matched_resource_id', sa.UUID(as_uuid=True), nullable=True),
        sa.Column('eta_minutes', sa.Integer, nullable=True),
        sa.Column('distance_km', sa.Float, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )

    # Spatial indexes for GPS queries
    op.create_index('ngo_res_loc_idx', 'ngo_resources', ['depot_location'], postgresql_using='gist')
    op.create_index('user_rep_gps_idx', 'user_reports', ['user_gps'], postgresql_using='gist')


def downgrade() -> None:
    op.drop_index('user_rep_gps_idx', table_name='user_reports')
    op.drop_index('ngo_res_loc_idx', table_name='ngo_resources')
    op.drop_table('user_reports')
    op.drop_table('ngo_resources')
    op.drop_table('ngo_users')