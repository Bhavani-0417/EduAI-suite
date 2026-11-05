import os

# Set required settings before importing application models/schemas in this isolated test.
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test-auth-schema.db")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret")
os.environ.setdefault("GOOGLE_API_KEY", "test-google-key")
os.environ.setdefault("CLOUDINARY_CLOUD_NAME", "test-cloud")
os.environ.setdefault("CLOUDINARY_API_KEY", "test-cloudinary-key")
os.environ.setdefault("CLOUDINARY_API_SECRET", "test-cloudinary-secret")

import pytest
from pydantic import ValidationError

from app.models.user import Branch
from app.schemas.auth_schema import RegisterRequest


def valid_payload():
    return {
        "name": "Test Student",
        "email": "student@example.com",
        "password": "correct horse battery staple",
        "college_id": "college-uuid",
        "branch": "btech_aids",
        "year": 4,
    }


def test_registration_accepts_supported_branch_and_year():
    request = RegisterRequest(**valid_payload())
    assert request.branch is Branch.BTECH_AIDS
    assert request.year == 4


def test_registration_rejects_client_supplied_role():
    payload = valid_payload()
    payload["role"] = "admin"
    with pytest.raises(ValidationError):
        RegisterRequest(**payload)


@pytest.mark.parametrize("password", ["short", "a" * 73])
def test_registration_rejects_password_outside_bcrypt_limits(password):
    payload = valid_payload()
    payload["password"] = password
    with pytest.raises(ValidationError):
        RegisterRequest(**payload)


def test_registration_rejects_unknown_branch_and_out_of_range_year():
    payload = valid_payload()
    payload["branch"] = "AI&DS"
    with pytest.raises(ValidationError):
        RegisterRequest(**payload)

    payload = valid_payload()
    payload["year"] = 5
    with pytest.raises(ValidationError):
        RegisterRequest(**payload)
