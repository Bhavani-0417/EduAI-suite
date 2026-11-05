import pytest

from app.services.vault.encryption_service import (
    NOTES_CIPHERTEXT_PREFIX,
    decrypt_notes_text,
    encrypt_notes_text,
)


def test_notes_text_is_encrypted_and_round_trips():
    plain_text = "Student record: example academic notes"
    encrypted = encrypt_notes_text(plain_text)
    assert encrypted.startswith(NOTES_CIPHERTEXT_PREFIX)
    assert plain_text not in encrypted
    assert decrypt_notes_text(encrypted) == plain_text


def test_notes_encryption_handles_none_and_empty_values():
    assert encrypt_notes_text(None) is None
    assert encrypt_notes_text("") is None
    assert decrypt_notes_text(None) is None


def test_legacy_plaintext_remains_readable_until_migration():
    assert decrypt_notes_text("legacy note content") == "legacy note content"


def test_tampered_notes_ciphertext_is_not_returned_as_plaintext():
    encrypted = encrypt_notes_text("private note")
    tampered = encrypted[:-2] + "AA"
    with pytest.raises(Exception):
        decrypt_notes_text(tampered)
