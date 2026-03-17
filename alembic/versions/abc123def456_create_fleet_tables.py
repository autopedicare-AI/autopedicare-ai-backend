"""create fleet tables

Revision ID: abc123def456
Revises: 26c7605dedad
Create Date: 2026-03-16 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'abc123def456'
down_revision: str = '26c7605dedad'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create enum types
    op.execute("""
    DO $$ BEGIN
        CREATE TYPE vehiclestatus AS ENUM ('active', 'maintenance', 'inactive');
    EXCEPTION
        WHEN duplicate_object THEN null;
    END $$;
    """)
    op.execute("""
    DO $$ BEGIN
        CREATE TYPE driverstatus AS ENUM ('active', 'inactive');
    EXCEPTION
        WHEN duplicate_object THEN null;
    END $$;
    """)
    op.execute("""
    DO $$ BEGIN
        CREATE TYPE assignmentstatus AS ENUM ('active', 'inactive');
    EXCEPTION
        WHEN duplicate_object THEN null;
    END $$;
    """)
    op.execute("""
    DO $$ BEGIN
        CREATE TYPE tripstatus AS ENUM ('ongoing', 'completed', 'cancelled');
    EXCEPTION
        WHEN duplicate_object THEN null;
    END $$;
    """)

    # Define enum types for table columns
    vehicle_status = sa.Enum('active', 'maintenance', 'inactive', name='vehiclestatus')
    driver_status = sa.Enum('active', 'inactive', name='driverstatus')
    assignment_status = sa.Enum('active', 'inactive', name='assignmentstatus')
    trip_status = sa.Enum('ongoing', 'completed', 'cancelled', name='tripstatus')

    # Create vehicles table
    op.create_table('vehicles',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('plate_number', sa.String(), nullable=False),
    sa.Column('model', sa.String(), nullable=False),
    sa.Column('manufacturer', sa.String(), nullable=False),
    sa.Column('year', sa.Integer(), nullable=False),
    sa.Column('vehicle_type', sa.String(), nullable=False),
    sa.Column('status', vehicle_status, nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('plate_number')
    )

    # Create drivers table
    op.create_table('drivers',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('full_name', sa.String(), nullable=False),
    sa.Column('license_number', sa.String(), nullable=False),
    sa.Column('phone_number', sa.String(), nullable=False),
    sa.Column('email', sa.String(), nullable=False),
    sa.Column('status', driver_status, nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('license_number'),
    sa.UniqueConstraint('email')
    )

    # Create assignments table
    op.create_table('assignments',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('driver_id', sa.UUID(), nullable=False),
    sa.Column('vehicle_id', sa.UUID(), nullable=False),
    sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('status', assignment_status, nullable=False),
    sa.ForeignKeyConstraint(['driver_id'], ['drivers.id'], ),
    sa.ForeignKeyConstraint(['vehicle_id'], ['vehicles.id'], ),
    sa.PrimaryKeyConstraint('id')
    )

    # Create trips table
    op.create_table('trips',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('driver_id', sa.UUID(), nullable=False),
    sa.Column('vehicle_id', sa.UUID(), nullable=False),
    sa.Column('start_location', sa.String(), nullable=False),
    sa.Column('end_location', sa.String(), nullable=False),
    sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
    sa.Column('end_time', sa.DateTime(timezone=True), nullable=True),
    sa.Column('distance_km', sa.Float(), nullable=False),
    sa.Column('status', trip_status, nullable=False),
    sa.ForeignKeyConstraint(['driver_id'], ['drivers.id'], ),
    sa.ForeignKeyConstraint(['vehicle_id'], ['vehicles.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('trips')
    op.drop_table('assignments')
    op.drop_table('drivers')
    op.drop_table('vehicles')

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS tripstatus")
    op.execute("DROP TYPE IF EXISTS assignmentstatus")
    op.execute("DROP TYPE IF EXISTS driverstatus")
    op.execute("DROP TYPE IF EXISTS vehiclestatus")