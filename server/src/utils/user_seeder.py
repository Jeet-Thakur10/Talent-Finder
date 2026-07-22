from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.models.postgres.user import User
from src.utils.crypt import hash_password


class UserSeeder:
    @staticmethod
    async def seed(db: AsyncSession) -> None:

        users = [
            {
                "name": "Recruiter",
                "email": "11a08cnn@gmail.com",
                "password": "Temppass@123",
                "role": "recruiter",
            },
            {
                "name": "Hiring Manager",
                "email": "jeetthakurofficialz@gmail.com",
                "password": "Password@123",
                "role": "hiring_manager",
            },
        ]

        for data in users:
            stmt = select(User).where(
                User.email == data["email"],
            )

            result = await db.execute(stmt)

            existing_user = result.scalar_one_or_none()

            if existing_user:
                continue

            db.add(
                User(
                    name=data["name"],
                    email=data["email"],
                    password_hash=hash_password(
                        data["password"],
                    ),
                    role=data["role"],
                    created_at=datetime.now(),
                )
            )

        await db.commit()
