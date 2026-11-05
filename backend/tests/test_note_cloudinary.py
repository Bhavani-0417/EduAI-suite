import pytest

from app.utils.note_cloudinary import (
    CLOUDINARY_AUTH_REF_PREFIX,
    decode_authenticated_asset,
    encode_authenticated_asset,
    resolve_note_asset_url,
)


def sample_upload():
    return {
        "public_id": "eduai/notes/student-123/asset-uuid_notes",
        "resource_type": "image",
        "format": "pdf",
        "type": "authenticated",
        "secure_url": "https://res.cloudinary.com/example/image/authenticated/private.pdf",
    }


def test_stores_authenticated_locator_not_the_public_cdn_url():
    stored = encode_authenticated_asset(sample_upload())
    assert stored.startswith(CLOUDINARY_AUTH_REF_PREFIX)
    assert "https://res.cloudinary.com" not in stored
    assert decode_authenticated_asset(stored) == {
        "public_id": sample_upload()["public_id"],
        "resource_type": "image",
        "format": "pdf",
        "type": "authenticated",
    }


def test_resolver_mints_a_short_lived_authenticated_url():
    stored = encode_authenticated_asset(sample_upload())
    captured = {}

    def fake_signer(public_id, file_format, **options):
        captured.update(public_id=public_id, file_format=file_format, **options)
        return "https://signed.example/download"

    url = resolve_note_asset_url(
        stored,
        private_download_url=fake_signer,
        now=1000,
        expires_in_seconds=300,
    )

    assert url == "https://signed.example/download"
    assert captured == {
        "public_id": sample_upload()["public_id"],
        "file_format": "pdf",
        "resource_type": "image",
        "type": "authenticated",
        "expires_at": 1300,
    }


def test_legacy_public_urls_are_not_re_emitted_by_the_api():
    assert resolve_note_asset_url("https://res.cloudinary.com/example/public.pdf", "pdf") is None


@pytest.mark.parametrize("expiry", [59, 3601])
def test_rejects_unsafe_signed_url_expiry(expiry):
    stored = encode_authenticated_asset(sample_upload())
    with pytest.raises(ValueError, match="expiry"):
        resolve_note_asset_url(stored, now=1000, expires_in_seconds=expiry)


def test_rejects_malformed_or_incomplete_authenticated_reference():
    with pytest.raises(ValueError):
        decode_authenticated_asset(CLOUDINARY_AUTH_REF_PREFIX + "{not-json}")
    with pytest.raises(ValueError):
        decode_authenticated_asset(CLOUDINARY_AUTH_REF_PREFIX + '{"public_id":"x"}')


def test_rejects_upload_responses_missing_asset_metadata():
    with pytest.raises(ValueError):
        encode_authenticated_asset({"public_id": "asset"})
