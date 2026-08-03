"""initial_schema

Revision ID: 000000000000
Revises: 
Create Date: 2026-06-25 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "000000000000"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. users
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    # 2. employment_types
    op.create_table(
        "employment_types",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
        sa.UniqueConstraint("name"),
    )

    # 3. job_description_statuses
    op.create_table(
        "job_description_statuses",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
        sa.UniqueConstraint("name"),
    )

    # 4. job_descriptions
    op.create_table(
        "job_descriptions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("recruiter_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("department", sa.String(), nullable=True),
        sa.Column("job_purpose", sa.Text(), nullable=False),
        sa.Column("responsibilities", sa.Text(), nullable=False),
        sa.Column("min_experience", sa.Integer(), nullable=False),
        sa.Column("max_experience", sa.Integer(), nullable=False),
        sa.Column("location", sa.String(), nullable=False),
        sa.Column("employment_type_id", sa.Uuid(), nullable=False),
        sa.Column("education_requirement", sa.String(), nullable=False),
        sa.Column("preferred_qualifications", sa.Text(), nullable=True),
        sa.Column("status_id", sa.Uuid(), nullable=False),
        sa.Column("hiring_manager_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["employment_type_id"], ["employment_types.id"]),
        sa.ForeignKeyConstraint(["hiring_manager_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["recruiter_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["status_id"], ["job_description_statuses.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # 5. jd_skills
    op.create_table(
        "jd_skills",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("jd_id", sa.Uuid(), nullable=False),
        sa.Column("skill_name", sa.String(), nullable=False),
        sa.Column("is_mandatory", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["jd_id"], ["job_descriptions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # 6. candidates
    op.create_table(
        "candidates",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("full_name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("current_title", sa.String(), nullable=True),
        sa.Column("location", sa.String(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("resume_text", sa.Text(), nullable=False),
        sa.Column("resume_hash", sa.String(), nullable=False),
        sa.Column("source_type", sa.String(), nullable=False),
        sa.Column("total_experience_months", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("resume_hash"),
    )

    # 7. candidate_skills
    op.create_table(
        "candidate_skills",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("candidate_id", sa.Uuid(), nullable=False),
        sa.Column("skill_name", sa.String(), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # 8. candidate_experiences
    op.create_table(
        "candidate_experiences",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("candidate_id", sa.Uuid(), nullable=False),
        sa.Column("company_name", sa.String(), nullable=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("is_current", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # 9. candidate_experience_skills
    op.create_table(
        "candidate_experience_skills",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("experience_id", sa.Uuid(), nullable=False),
        sa.Column("skill_name", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["experience_id"], ["candidate_experiences.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # 10. candidate_educations
    op.create_table(
        "candidate_educations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("candidate_id", sa.Uuid(), nullable=False),
        sa.Column("institution_name", sa.String(), nullable=True),
        sa.Column("degree", sa.String(), nullable=False),
        sa.Column("field_of_study", sa.String(), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # 11. candidate_job_scores
    op.create_table(
        "candidate_job_scores",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("candidate_id", sa.Uuid(), nullable=False),
        sa.Column("job_description_id", sa.Uuid(), nullable=False),
        sa.Column("final_score", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("skills_score", sa.Float(), nullable=False),
        sa.Column("experience_score", sa.Float(), nullable=False),
        sa.Column("recency_score", sa.Float(), nullable=False),
        sa.Column("role_fit_score", sa.Float(), nullable=False),
        sa.Column("education_score", sa.Float(), nullable=False),
        sa.Column("matched_mandatory_skills", sa.JSON(), nullable=False),
        sa.Column("matched_optional_skills", sa.JSON(), nullable=False),
        sa.Column("missing_mandatory_skills", sa.JSON(), nullable=False),
        sa.Column("explanation", sa.JSON(), nullable=False),
        sa.Column("relevance_status", sa.String(length=32), server_default="RELEVANT", nullable=False),
        sa.Column("relevance_reason", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"]),
        sa.ForeignKeyConstraint(["job_description_id"], ["job_descriptions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("candidate_id", "job_description_id", name="uq_candidate_job_score_candidate_job"),
    )

    # 12. pipeline
    op.create_table(
        "pipeline",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("candidate_id", sa.Uuid(), nullable=False),
        sa.Column("jd_id", sa.Uuid(), nullable=False),
        sa.Column("stage", sa.String(), nullable=False),
        sa.Column("recruiter_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"]),
        sa.ForeignKeyConstraint(["jd_id"], ["job_descriptions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("candidate_id", "jd_id", name="uq_pipeline_candidate_jd"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("pipeline")
    op.drop_table("candidate_job_scores")
    op.drop_table("candidate_educations")
    op.drop_table("candidate_experience_skills")
    op.drop_table("candidate_experiences")
    op.drop_table("candidate_skills")
    op.drop_table("candidates")
    op.drop_table("jd_skills")
    op.drop_table("job_descriptions")
    op.drop_table("job_description_statuses")
    op.drop_table("employment_types")
    op.drop_table("users")
