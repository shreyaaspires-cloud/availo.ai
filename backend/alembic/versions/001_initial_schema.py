"""initial_schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-28 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Enable pgcrypto extension for gen_random_uuid()
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    # 2. Users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('roles', sa.ARRAY(sa.String()), nullable=False),
        sa.Column('trust_score', sa.Float(), server_default='100.0', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # 3. Verification Badges table
    op.create_table(
        'verification_badges',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('badge_type', sa.Enum('STUDENT', 'RESEARCHER', 'PROFESSIONAL', 'FACULTY', name='badge_type_enum'), nullable=False),
        sa.Column('document_url', sa.String(length=1024), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'APPROVED', 'REJECTED', name='badge_status_enum'), nullable=False),
        sa.Column('admin_note', sa.String(length=1000), nullable=True),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_verification_badges_user_id'), 'verification_badges', ['user_id'], unique=False)

    # 4. Resources table
    op.create_table(
        'resources',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('location', sa.String(length=300), nullable=False),
        sa.Column('daily_rate', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('deposit_amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('max_booking_days', sa.Integer(), nullable=False),
        sa.Column('requires_badge', sa.ARRAY(sa.String()), nullable=False),
        sa.Column('condition', sa.Text(), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('fair_use_limit_per_week', sa.Integer(), server_default='2', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_resources_category'), 'resources', ['category'], unique=False)
    op.create_index(op.f('ix_resources_owner_id'), 'resources', ['owner_id'], unique=False)
    op.create_index(op.f('ix_resources_title'), 'resources', ['title'], unique=False)

    # Full-text search index on resources
    op.execute(
        "CREATE INDEX idx_resources_fts ON resources USING gin(to_tsvector('english', title || ' ' || description || ' ' || location))"
    )

    # 5. Resource Images table
    op.create_table(
        'resource_images',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('url', sa.String(length=1024), nullable=False),
        sa.Column('angle', sa.Enum('FRONT', 'BACK', 'LEFT', 'RIGHT', 'TOP', 'BOTTOM', name='image_angle_enum'), nullable=False),
        sa.Column('is_primary', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['resource_id'], ['resources.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 6. Availability Slots table
    op.create_table(
        'availability_slots',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('start_dt', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_dt', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_blocked', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['resource_id'], ['resources.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 7. Bookings table
    op.create_table(
        'bookings',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.Enum(
            'DRAFT', 'PENDING_APPROVAL', 'APPROVED', 'REJECTED', 'WAITLISTED',
            'AWAITING_SIGNATURES', 'AWAITING_PAYMENT', 'CONFIRMED', 'CHECKED_IN',
            'RETURN_SUBMITTED', 'DAMAGE_REVIEW', 'DISPUTE_OPEN', 'RESOLVED_OWNER',
            'RESOLVED_USER', 'RESOLVED_SPLIT', 'COMPLETED', 'CANCELLED',
            name='booking_status_enum'
        ), nullable=False),
        sa.Column('start_dt', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_dt', sa.DateTime(timezone=True), nullable=False),
        sa.Column('purpose', sa.Text(), nullable=False),
        sa.Column('total_amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('deposit_amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('cancellation_reason', sa.Text(), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('payment_reference', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['resource_id'], ['resources.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_bookings_status'), 'bookings', ['status'], unique=False)

    # 8. Waitlist Entries
    op.create_table(
        'waitlist_entries',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('requested_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('requested_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('notified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['resource_id'], ['resources.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 9. Condition Reports table
    op.create_table(
        'condition_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('booking_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('report_type', sa.Enum('CHECK_IN', 'CHECK_OUT', name='report_type_enum'), nullable=False),
        sa.Column('submitted_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['booking_id'], ['bookings.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('booking_id', 'report_type', name='uq_booking_report_type')
    )

    # 10. Condition Images table
    op.create_table(
        'condition_images',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('report_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('url', sa.String(length=1024), nullable=False),
        sa.Column('angle', sa.Enum('FRONT', 'BACK', 'LEFT', 'RIGHT', 'TOP', 'BOTTOM', name='condition_image_angle_enum'), nullable=False),
        sa.Column('exif_timestamp', sa.DateTime(timezone=True), nullable=True),
        sa.Column('exif_gps_lat', sa.Float(), nullable=True),
        sa.Column('exif_gps_lon', sa.Float(), nullable=True),
        sa.Column('fingerprint', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['report_id'], ['condition_reports.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 11. Contracts table
    op.create_table(
        'contracts',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('booking_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content_html', sa.Text(), nullable=False),
        sa.Column('pdf_url', sa.String(length=1024), nullable=True),
        sa.Column('sha256_hash', sa.String(length=64), nullable=True),
        sa.Column('status', sa.Enum('DRAFT', 'PENDING_SIGNATURES', 'SIGNED', 'VOIDED', name='contract_status_enum'), nullable=False),
        sa.Column('generated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['booking_id'], ['bookings.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('booking_id')
    )

    # 12. Contract Signatures table
    op.create_table(
        'contract_signatures',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('contract_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role_in_contract', sa.Enum('USER', 'OWNER', name='contract_signer_role_enum'), nullable=False),
        sa.Column('signature_image_url', sa.String(length=1024), nullable=False),
        sa.Column('signed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(['contract_id'], ['contracts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 13. Incident Reports table
    op.create_table(
        'incident_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('booking_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('raised_by_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.Enum('OPEN', 'UNDER_REVIEW', 'RESOLVED_OWNER', 'RESOLVED_USER', 'RESOLVED_SPLIT', name='incident_status_enum'), nullable=False),
        sa.Column('resolution_note', sa.Text(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['booking_id'], ['bookings.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['raised_by_id'], ['users.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('booking_id')
    )

    # 14. Damage Assessments table
    op.create_table(
        'damage_assessments',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('incident_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('angle', sa.Enum('FRONT', 'BACK', 'LEFT', 'RIGHT', 'TOP', 'BOTTOM', name='damage_angle_enum'), nullable=False),
        sa.Column('before_image_url', sa.String(length=1024), nullable=False),
        sa.Column('after_image_url', sa.String(length=1024), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=False),
        sa.Column('anomalies', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('closeup_required', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('closeup_image_url', sa.String(length=1024), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['incident_id'], ['incident_reports.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 15. Chat Rooms & Messages
    op.create_table(
        'chat_rooms',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('booking_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['booking_id'], ['bookings.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('booking_id')
    )
    op.create_table(
        'chat_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('room_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sender_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('attachment_url', sa.String(length=1024), nullable=True),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['room_id'], ['chat_rooms.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['sender_id'], ['users.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )

    # 16. Notifications table
    op.create_table(
        'notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('type', sa.String(length=100), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('is_read', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('related_booking_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['related_booking_id'], ['bookings.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 17. Append-only Audit Logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('booking_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('previous_status', sa.String(length=50), nullable=True),
        sa.Column('new_status', sa.String(length=50), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['booking_id'], ['bookings.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # Enforce append-only on audit_logs via Postgres Trigger
    op.execute("""
        CREATE OR REPLACE FUNCTION enforce_audit_logs_append_only()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'Updates and deletions are strictly forbidden on audit_logs table';
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trg_audit_logs_append_only
        BEFORE UPDATE OR DELETE ON audit_logs
        FOR EACH ROW
        EXECUTE FUNCTION enforce_audit_logs_append_only();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_audit_logs_append_only ON audit_logs")
    op.execute("DROP FUNCTION IF EXISTS enforce_audit_logs_append_only")
    op.drop_table('audit_logs')
    op.drop_table('notifications')
    op.drop_table('chat_messages')
    op.drop_table('chat_rooms')
    op.drop_table('damage_assessments')
    op.drop_table('incident_reports')
    op.drop_table('contract_signatures')
    op.drop_table('contracts')
    op.drop_table('condition_images')
    op.drop_table('condition_reports')
    op.drop_table('waitlist_entries')
    op.drop_table('bookings')
    op.drop_table('availability_slots')
    op.drop_table('resource_images')
    op.drop_table('resources')
    op.drop_table('verification_badges')
    op.drop_table('users')
