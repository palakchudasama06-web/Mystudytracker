import hashlib
import hmac
import os


def hash_password(password: str) -> str:
    """PBKDF2 password hashing using Python's standard library."""
    salt = os.urandom(16)
    iterations = 310_000
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)
    return f"pbkdf2_sha256${iterations}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algorithm, iterations, salt_hex, digest_hex = stored.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode(),
            bytes.fromhex(salt_hex),
            int(iterations),
        )
        return hmac.compare_digest(digest.hex(), digest_hex)
    except Exception:
        return False


def xp_for_minutes(minutes):
    return max(10, int(minutes) * 2)


def level_from_xp(xp):
    level = max(1, xp // 1000 + 1)
    current = xp % 1000
    return level, current, 1000


def motivational_message(hours, streak):
    if hours == 0 and streak == 0:
        return "You do not need a perfect day. You only need to start. One focused session can change today's direction."
    if hours == 0:
        return f"Your {streak}-day consistency is waiting for you. Protect the streak with one small study session today."
    if hours < 1:
        return "You showed up. Now protect that momentum with one more focused block."
    if hours < 3:
        return "Articleship can drain your energy, but you still made time. That consistency is what compounds."
    return "Excellent work. You are building the kind of consistency that survives busy articleship days."
