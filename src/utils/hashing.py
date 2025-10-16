import bcrypt

def truncate_utf8(s: str, max_bytes: int = 72) -> str:
    """Truncate string to max_bytes UTF-8 encoded length."""
    encoded = s.encode('utf-8')
    if len(encoded) <= max_bytes:
        return s
    return encoded[:max_bytes].decode('utf-8', errors='ignore')

def verify_password(plain: str, hashed: str) -> bool:
    print(f"Verifying password. Plain: {plain}, Hashed: {hashed}")
    # Apply same truncation during verification
    truncated = truncate_utf8(plain, 72)
    try:
        # Convert password to bytes
        password_bytes = truncated.encode('utf-8')
        # Convert hashed to bytes if it's stored as string
        hashed_bytes = hashed.encode('utf-8') if isinstance(hashed, str) else hashed
        # Verify the password
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except ValueError as e:
        print(f"Password verification error: {str(e)}")
        return False
    except Exception as e:
        print(f"Unexpected error during password verification: {str(e)}")
        return False

def get_password_hash(password: str) -> str:
    # Truncate password before hashing to ensure bcrypt limit
    truncated = truncate_utf8(password, 72)
    # Generate salt (using work factor of 12 for good security/performance balance)
    salt = bcrypt.gensalt(rounds=12)
    # Hash password
    password_bytes = truncated.encode('utf-8')
    hashed = bcrypt.hashpw(password_bytes, salt)
    # Return as string for storage (will be in format $2b$12$[22 characters of salt][31 characters of hash])
    return hashed.decode('utf-8')