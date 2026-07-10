import asyncio
import sys
import uuid

import httpx
from httpx import AsyncClient

from main import app


async def test_add_recruiter_flow():
    transport = httpx.ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Login as Recruiter
        print("Logging in as Recruiter...")
        login_response = await client.post(
            "/auth/login",
            json={"email": "11a08cnn@gmail.com", "password": "Temppass@123"},
        )
        assert login_response.status_code == 200, f"Recruiter login failed: {login_response.text}"
        print("Logged in as Recruiter successfully.")

        # Generates a random email to test creation
        unique_id = str(uuid.uuid4())[:8]
        new_email = f"new_recruiter_{unique_id}@company.com"
        new_user_data = {
            "name": f"Test Recruiter {unique_id}",
            "email": new_email,
            "role": "recruiter",
            "password": "SecurePassword@123"
        }

        # 2. Create a new user (Recruiter)
        print(f"\nTesting POST /auth/users (Create User) with email: {new_email}...")
        create_response = await client.post("/auth/users", json=new_user_data)
        assert create_response.status_code == 200, f"Failed to create user: {create_response.text}"
        user_data = create_response.json()
        
        # Verify returned user fields
        assert "id" in user_data
        assert user_data["name"] == new_user_data["name"]
        assert user_data["email"] == new_user_data["email"]
        assert user_data["role"] == "recruiter"
        # Ensure sensitive info such as password_hash is not returned
        assert "password_hash" not in user_data
        assert "password" not in user_data
        print("User created successfully. Payload returned correctly without password hashes.")

        # 3. Create a user with duplicate email (should fail with 400)
        print("\nTesting POST /auth/users with duplicate email...")
        dup_response = await client.post("/auth/users", json=new_user_data)
        assert dup_response.status_code == 400, f"Expected 400 for duplicate email, got {dup_response.status_code}"
        dup_json = dup_response.json()
        assert "email already exists" in dup_json["detail"].lower()
        print("Duplicate email caught successfully with 400 Bad Request.")

        # 4. Create a user with invalid password complexity (should fail with 400)
        print("\nTesting POST /auth/users with weak password...")
        weak_user_data = new_user_data.copy()
        weak_user_data["email"] = f"weak_{unique_id}@company.com"
        weak_user_data["password"] = "weak"  # No special char and too short
        weak_response = await client.post("/auth/users", json=weak_user_data)
        assert weak_response.status_code == 400, f"Expected 400 for weak password, got {weak_response.status_code}"
        weak_json = weak_response.json()
        assert "invalid password" in weak_json["detail"].lower()
        print("Weak password complexity caught successfully with 400 Bad Request.")

        # 5. Log out recruiter
        print("\nLogging out recruiter...")
        await client.post("/auth/logout")

        # 6. Log in as Hiring Manager
        print("\nLogging in as Hiring Manager...")
        hm_login_response = await client.post(
            "/auth/login",
            json={"email": "jeetthakurofficialz@gmail.com", "password": "Password@123"},
        )
        assert hm_login_response.status_code == 200, f"Hiring Manager login failed: {hm_login_response.text}"
        print("Logged in as Hiring Manager successfully.")

        # 7. Try to create a user as Hiring Manager (should fail with 400/403 RecruiterAccessRequired)
        print("\nTesting POST /auth/users as Hiring Manager (unauthorized role)...")
        unauth_user_data = new_user_data.copy()
        unauth_user_data["email"] = f"unauth_{unique_id}@company.com"
        unauth_response = await client.post("/auth/users", json=unauth_user_data)
        assert unauth_response.status_code == 400, f"Expected 400/403 for unauthorized access, got {unauth_response.status_code}"
        unauth_json = unauth_response.json()
        assert "recruiter access required" in unauth_json["detail"].lower()
        print("Unauthorized user creation properly blocked with RecruiterAccessRequired.")

        print("\nALL RECRUITER USER MANAGEMENT API TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    try:
        asyncio.run(test_add_recruiter_flow())
    except AssertionError as e:
        print(f"\n[FAIL] Test assertion failed: {e}")
        sys.exit(1)
    except Exception:
        import traceback
        traceback.print_exc()
        sys.exit(1)
