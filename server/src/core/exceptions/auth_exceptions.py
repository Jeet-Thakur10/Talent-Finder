class AuthBaseException(Exception):
    """Base for all auth-related exceptions."""
    def __init__(self, message: str, details: str = None, error_code: str | None = None):
        self.message = message
        self.details = details
        self.error_code = error_code

        super().__init__(self.message)


class InvalidToken(AuthBaseException):
    def __init__(self, details: str = None, error_code: str = None):
        super().__init__(message="Invalid or expired token", details=details, error_code=error_code)


class InvalidAuthorizationFormat(AuthBaseException):
    def __init__(self, details: str = None):
        super().__init__(message="Invalid authorization header format", details=details)


class GeneralException(AuthBaseException):
    def __init__(self, details: str = None):
        super().__init__(message="An unexpected error occurred", details=details)

class InvalidPasswordException(AuthBaseException):
    def __init__(self, details: str = None):
        super().__init__(
            message="Invalid password",
            details=details or (
                "Password must be at least 8 characters long "
                "and contain at least 1 special character."
            )
        )

class UserAlreadyExistsException(AuthBaseException):
    def __init__(self, details: str = None):
        super().__init__(
            message="A user with this email already exists",
            details=details
        )

class InvalidCredentials(AuthBaseException):
    def __init__(self, details: str = None):
        super().__init__(
            message="Invalid email",
            details=details
        )