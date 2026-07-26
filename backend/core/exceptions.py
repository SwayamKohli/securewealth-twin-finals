class AuthenticationError(Exception):
    """Raised when authentication fails."""


class UserAlreadyExistsError(Exception):
    """Raised when phone number already exists."""


class UserNotFoundError(Exception):
    """Raised when user does not exist."""


class CredentialsNotFoundError(Exception):
    """Raised when auth credentials are missing."""