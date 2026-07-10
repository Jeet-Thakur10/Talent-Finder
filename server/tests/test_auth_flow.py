import asyncio
import sys

import httpx
from httpx import AsyncClient

from main import app


async def test_auth_flow():
    transport = httpx.ASGITransport(app=app)
    # Use AsyncClient to run on the main async loop, preventing any thread conflicts with asyncpg
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Login
        login_data = {"email": "11a08cnn@gmail.com", "password": "Temppass@123"}
        print("Testing POST /auth/login...")
        response = await client.post("/auth/login", json=login_data)
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.text}"
        )
        data = response.json()
        assert "user" in data, "Expected 'user' in response"
        user = data["user"]
        assert user["email"] == login_data["email"]
        assert user["role"] == "recruiter"
        assert "id" in user
        print("Login successful, user details returned:", user)

        # Check cookies
        cookies = response.cookies
        assert "access_token" in cookies, "access_token cookie missing"
        assert "refresh_token" in cookies, "refresh_token cookie missing"
        print("Cookies set successfully.")

        # 2. Test GET /auth/me
        print("\nTesting GET /auth/me...")
        response = await client.get("/auth/me")
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.text}"
        )
        me_data = response.json()
        print("GET /auth/me returned:", me_data)
        assert me_data["email"] == login_data["email"]
        assert me_data["role"] == "recruiter"
        assert "id" in me_data
        assert "name" in me_data
        print("GET /auth/me returns full user details successfully!")

        # 3. Test POST /auth/refresh
        print("\nTesting POST /auth/refresh...")
        response = await client.post("/auth/refresh")
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.text}"
        )
        refresh_data = response.json()
        print("POST /auth/refresh returned:", refresh_data)
        assert "message" in refresh_data
        assert "access_token" in client.cookies, (
            "access_token cookie missing after refresh"
        )
        print("Token refreshed successfully.")

        # 4. Test POST /auth/logout
        print("\nTesting POST /auth/logout...")
        response = await client.post("/auth/logout")
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.text}"
        )
        print("Logout successful.")

        # 5. Test GET /auth/me after logout (should fail with 401)
        print("\nTesting GET /auth/me after logout...")
        response = await client.get("/auth/me")
        assert response.status_code == 401, (
            f"Expected 401, got {response.status_code}: {response.text}"
        )
        print("GET /auth/me properly unauthorized after logout!")

        print("\nALL AUTH FLOW TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    try:
        asyncio.run(test_auth_flow())
    except AssertionError as e:
        print(f"\n[FAIL] Test assertion failed: {e}")
        sys.exit(1)
    except Exception:
        import traceback

        traceback.print_exc()
        sys.exit(1)
