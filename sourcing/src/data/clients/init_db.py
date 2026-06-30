from src.data.clients.postgres import (
    Base,
    engine,
)

# Import all models so SQLAlchemy registers them
from src.data.models.postgres.candidate import Candidate
from src.data.models.postgres.candidate_skill import CandidateSkill
from src.data.models.postgres.candidate_experience import CandidateExperience
from src.data.models.postgres.candidate_experience_skill import (
    CandidateExperienceSkill,
)
from src.data.models.postgres.candidate_education import (
    CandidateEducation,
)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(
            Base.metadata.create_all,
        )