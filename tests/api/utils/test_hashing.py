import pytest

from src.utils.hashing import (
    get_password_hash,
    verify_password,
    truncate_utf8,
)


def test_roundtrip_ok():
    """Hashing a password and verifying the same password should return True."""
    pwd = "test_password"
    h = get_password_hash(pwd)
    assert isinstance(h, str) and len(h) > 0
    assert verify_password(pwd, h) is True


def test_wrong_password_returns_false():
    """Verifying with a wrong password should return False."""
    pwd = "correct_password"
    h = get_password_hash(pwd)
    assert verify_password("WRONG", h) is False


def test_salt_variation_same_password_produces_different_hashes():
    """Bcrypt uses random salt -> two hashes of the same password should differ."""
    pwd = "same_password"
    h1 = get_password_hash(pwd)
    h2 = get_password_hash(pwd)
    assert h1 != h2
    assert verify_password(pwd, h1) is True
    assert verify_password(pwd, h2) is True


def test_unicode_password_roundtrip():
    """Unicode passwords are supported and verify correctly."""
    pwd = "парольЄвро€"
    h = get_password_hash(pwd)
    assert verify_password(pwd, h) is True


def test_invalid_hash_returns_false():
    """verify_password should not crash on invalid hash strings; returns False."""
    pwd = "anything"
    invalid_hashes = [
        "not-a-bcrypt-hash",
        "",  # empty
        "$2b$12$short",  # malformed
        "2b$12$no-dollar-prefix",  # missing '$' prefix
    ]
    for ih in invalid_hashes:
        assert verify_password(pwd, ih) is False


def test_bcrypt_format_sanity():
    """
    get_password_hash should yield a bcrypt hash.
    Typical form: $2b$12$<22-char-salt><31-char-hash>
    Don't overfit length, but ensure a plausible prefix and overall structure.
    """
    h = get_password_hash("pwd")
    assert h.startswith(("$2b$", "$2a$", "$2y$"))
    # Contains cost and payload sections separated by '$'
    parts = h.split("$")
    assert len(parts) >= 4
    assert parts[2].isdigit()  # cost factor present


def test_truncate_utf8_multibyte_safety():
    """
    truncate_utf8 should never cut a multibyte character in the middle.
    Verify the result still encodes to valid UTF-8 and respects byte limit.
    """
    s = ("a" * 71) + "€"
    truncated = truncate_utf8(s, max_bytes=72)
    # Expect the '€' to be dropped to keep <=72 bytes
    assert truncated == "a" * 71
    assert len(truncated.encode("utf-8")) <= 72

    s2 = "𐍈" * 100  # each '𐍈' is 4 bytes in UTF-8
    t2 = truncate_utf8(s2, max_bytes=72)
    assert isinstance(t2, str)
    assert len(t2.encode("utf-8")) <= 72


def test_verify_truncation_compatibility_same_prefix_after_72_bytes():
    """
    Bcrypt only considers the first 72 bytes. Your implementation explicitly truncates to 72 bytes
    before hashing/verifying. Therefore, two passwords that differ only AFTER 72 bytes should verify
    the same if the hash was produced from the 72-byte prefix.

    This test documents the security nuance and ensures consistent behavior.
    """
    # Build a base that is exactly 72 bytes in UTF-8
    base = "a" * 72  # ASCII => 72 bytes
    # Hash is created from 'base'
    h = get_password_hash(base)

    # Candidate differs after 72 bytes (has extra suffix), but truncation removes it.
    candidate = base + "THIS_PART_IS_IGNORED"
    assert verify_password(candidate, h) is True

    # Sanity check: differing within the first 72 bytes should fail.
    altered_within_prefix = ("b" + "a" * 71)  # differs in the first byte
    assert verify_password(altered_within_prefix, h) is False


@pytest.mark.parametrize("max_bytes", [1, 2, 3, 10, 72, 100])
def test_truncate_never_exceeds_limit(max_bytes):
    """Encoded length of truncated string should never exceed max_bytes."""
    s = "αβγδ€" * 20  # lots of multibyte characters
    t = truncate_utf8(s, max_bytes=max_bytes)
    assert len(t.encode("utf-8")) <= max_bytes
