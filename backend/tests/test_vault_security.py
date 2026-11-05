from datetime import datetime, timedelta, timezone

from app.utils.vault_security import (
    as_utc_datetime,
    content_disposition_attachment,
    is_share_expired,
)


def test_naive_database_datetime_is_treated_as_utc():
    value = datetime(2026, 1, 1, 12, 0, 0)
    normalized = as_utc_datetime(value)
    assert normalized.tzinfo == timezone.utc
    assert normalized == value.replace(tzinfo=timezone.utc)


def test_aware_database_datetime_is_converted_to_utc():
    value = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone(timedelta(hours=5, minutes=30)))
    normalized = as_utc_datetime(value)
    assert normalized.hour == 6
    assert normalized.minute == 30
    assert normalized.tzinfo == timezone.utc


def test_share_expiry_works_for_naive_values_and_boundary():
    now = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    assert not is_share_expired(datetime(2026, 1, 1, 12, 1, 0), now)
    assert is_share_expired(datetime(2026, 1, 1, 12, 0, 0), now)
    assert is_share_expired(datetime(2026, 1, 1, 11, 59, 0), now)


def test_download_filename_is_safe_for_response_headers():
    header = content_disposition_attachment('report"\r\nX-Evil: yes.pdf')
    assert "\r" not in header
    assert "\n" not in header
    assert "X-Evil" not in header
    assert 'filename="download"' in header
    assert "filename*=UTF-8''" in header


def test_download_filename_handles_unicode_and_empty_names():
    header = content_disposition_attachment("విద్యార్థి మార్కులు.pdf")
    assert "%E0" in header
    assert content_disposition_attachment(None) == (
        "attachment; filename=\"download\"; filename*=UTF-8''download"
    )
