import re

from src.core.exceptions.auth_exceptions import InvalidPasswordException


def validate_password(password: str) -> None:

    if len(password) < 8:
        raise InvalidPasswordException()

    special_character_pattern = r"[!@#$%^&*(),.?\":{}|<>_\-\\/\[\]=+;']"

    if not re.search(special_character_pattern, password):
        raise InvalidPasswordException()
