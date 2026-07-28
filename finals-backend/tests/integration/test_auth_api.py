"""Integration tests for Auth API endpoints."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestAuthRegister:
    async def test_register_creates_org_and_user(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "org_name": "Test Corp",
                "industry": "technology",
                "email": "admin@testcorp.com",
                "username": "testadmin",
                "password": "SecurePass123!",
                "full_name": "Test Admin",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "org_id" in data
        assert data["user"]["role"] == "org_admin"

    async def test_register_duplicate_email_fails(self, client: AsyncClient):
        payload = {
            "org_name": "Dup Corp",
            "industry": "technology",
            "email": "dup@dup.com",
            "username": "dupuser1",
            "password": "SecurePass123!",
            "full_name": "Dup User",
        }
        # First registration
        r1 = await client.post("/api/v1/auth/register", json=payload)
        assert r1.status_code == 201

        # Second registration with same email
        payload["username"] = "dupuser2"
        payload["org_name"] = "Dup Corp 2"
        r2 = await client.post("/api/v1/auth/register", json=payload)
        assert r2.status_code == 409

    async def test_register_weak_password_rejected(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "org_name": "Test",
                "industry": "tech",
                "email": "weak@test.com",
                "username": "weakuser",
                "password": "123",
                "full_name": "Weak",
            },
        )
        assert resp.status_code == 422


@pytest.mark.asyncio
class TestAuthLogin:
    async def test_login_returns_tokens(self, client: AsyncClient):
        # Register first
        await client.post(
            "/api/v1/auth/register",
            json={
                "org_name": "Login Corp",
                "industry": "finance",
                "email": "login@logincorp.com",
                "username": "loginuser",
                "password": "SecurePass123!",
                "full_name": "Login User",
            },
        )
        # Now login
        resp = await client.post(
            "/api/v1/auth/login",
            data={"username": "login@logincorp.com", "password": "SecurePass123!"},
        )
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    async def test_wrong_password_returns_401(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/auth/login",
            data={"username": "nonexistent@corp.com", "password": "wrongpassword"},
        )
        assert resp.status_code == 401
