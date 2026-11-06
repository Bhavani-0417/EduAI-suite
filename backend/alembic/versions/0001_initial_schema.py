"""Create the initial EduAI relational schema.

Revision ID: 0001_initial_schema
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None

branch_enum = postgresql.ENUM("BTECH_CS", "BTECH_AIDS", "BTECH_ECE", "MBBS", "INTERMEDIATE", "SCHOOL", "OTHER", name="branch")
user_role_enum = postgresql.ENUM("STUDENT", "FACULTY", "ADMIN", name="userrole")
note_source_enum = postgresql.ENUM("STUDENT", "FACULTY", name="notesource")
application_status_enum = postgresql.ENUM("APPLIED", "SHORTLISTED", "INTERVIEW", "OFFER", "REJECTED", name="applicationstatus")
event_type_enum = postgresql.ENUM("COLLEGE_EVENT", "HACKATHON", "WORKSHOP", "EXAM", "DEADLINE", name="eventtype")
document_type_enum = postgresql.ENUM("MARKSHEET", "CERTIFICATE", "TRANSCRIPT", "ID_CARD", "OFFER_LETTER", "OTHER", name="documenttype")


def upgrade() -> None:
    bind = op.get_bind()
    for enum_type in (branch_enum, user_role_enum, note_source_enum, application_status_enum, event_type_enum, document_type_enum):
        enum_type.create(bind, checkfirst=True)

    op.create_table(
        "colleges",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("university", sa.String(), nullable=True),
        sa.Column("city", sa.String(), nullable=True),
        sa.Column("state", sa.String(), nullable=True),
        sa.Column("college_code", sa.String(), nullable=True),
        sa.Column("primary_color", sa.String(), nullable=True),
        sa.Column("secondary_color", sa.String(), nullable=True),
        sa.Column("logo_url", sa.String(), nullable=True),
        sa.Column("header_text", sa.String(), nullable=True),
        sa.Column("footer_text", sa.String(), nullable=True),
        sa.Column("font_name", sa.String(), nullable=True),
        sa.Column("watermark_text", sa.String(), nullable=True),
        sa.Column("template_config", sa.JSON(), nullable=True),
        sa.Column("sso_config", sa.JSON(), nullable=True),
        sa.Column("has_sso", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("college_code"),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=True),
        sa.Column("full_name", sa.String(), nullable=False),
        sa.Column("college_id", sa.String(), nullable=True),
        sa.Column("student_roll_number", sa.String(), nullable=True),
        sa.Column("branch", postgresql.ENUM(name="branch", create_type=False), nullable=True),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("semester", sa.Integer(), nullable=True),
        sa.Column("city", sa.String(), nullable=True),
        sa.Column("role", postgresql.ENUM(name="userrole", create_type=False), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=True),
        sa.Column("google_id", sa.String(), nullable=True),
        sa.Column("profile_picture", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["college_id"], ["colleges.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_table(
        "marks",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("student_id", sa.String(), nullable=False),
        sa.Column("subject", sa.String(), nullable=False),
        sa.Column("semester", sa.Integer(), nullable=False),
        sa.Column("marks_obtained", sa.Float(), nullable=False),
        sa.Column("total_marks", sa.Float(), nullable=False),
        sa.Column("exam_type", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "notes",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("student_id", sa.String(), nullable=False),
        sa.Column("subject", sa.String(), nullable=True),
        sa.Column("topic", sa.String(), nullable=True),
        sa.Column("chapter", sa.String(), nullable=True),
        sa.Column("file_url", sa.String(), nullable=False),
        sa.Column("file_name", sa.String(), nullable=False),
        sa.Column("file_type", sa.String(), nullable=False),
        sa.Column("extracted_text", sa.Text(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("source", postgresql.ENUM(name="notesource", create_type=False), nullable=True),
        sa.Column("chroma_collection_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "job_applications",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("student_id", sa.String(), nullable=False),
        sa.Column("company", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("job_description", sa.Text(), nullable=True),
        sa.Column("resume_version_url", sa.String(), nullable=True),
        sa.Column("match_score", sa.Float(), nullable=True),
        sa.Column("status", postgresql.ENUM(name="applicationstatus", create_type=False), nullable=True),
        sa.Column("applied_date", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "roadmaps",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("student_id", sa.String(), nullable=False),
        sa.Column("goal", sa.String(), nullable=False),
        sa.Column("phases", sa.JSON(), nullable=False),
        sa.Column("progress_percent", sa.Float(), nullable=True),
        sa.Column("completed_topics", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "events",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("college_id", sa.String(), nullable=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("event_type", postgresql.ENUM(name="eventtype", create_type=False), nullable=False),
        sa.Column("event_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("location", sa.String(), nullable=True),
        sa.Column("city", sa.String(), nullable=True),
        sa.Column("registration_url", sa.String(), nullable=True),
        sa.Column("is_external", sa.Boolean(), nullable=True),
        sa.Column("tags", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["college_id"], ["colleges.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "vault_documents",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("student_id", sa.String(), nullable=False),
        sa.Column("doc_type", postgresql.ENUM(name="documenttype", create_type=False), nullable=False),
        sa.Column("file_name", sa.String(), nullable=False),
        sa.Column("encrypted_url", sa.String(), nullable=False),
        sa.Column("ocr_text", sa.Text(), nullable=True),
        sa.Column("share_token", sa.String(), nullable=True),
        sa.Column("share_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    for table in ("vault_documents", "events", "roadmaps", "job_applications", "notes", "marks"):
        op.drop_table(table)
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
    op.drop_table("colleges")
    bind = op.get_bind()
    for enum_type in (document_type_enum, event_type_enum, application_status_enum, note_source_enum, user_role_enum, branch_enum):
        enum_type.drop(bind, checkfirst=True)
