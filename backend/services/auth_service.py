from uuid import uuid4

from sqlalchemy.orm import Session

from core.security import (
    create_access_token,
    hash_mpin,
    verify_mpin,
)
from database.repositories.auth_repository import (
    AuthRepository,
)
from models.auth_credential import AuthCredential
from models.user import User
from core.exceptions import AuthenticationError
from schemas.auth_schema import (
    LoginRequest,
    LogoutResponse,
    RegisterRequest,
    RegisterResponse,
    SessionResponse,
    TokenResponse,
)


class AuthService:
    # Constructor
    def __init__(
        self,
        db: Session,
    ):

        self.repo = AuthRepository(db)

    # ── SecureWealth ID (CIF-style) generation ────────────────────────────
    def _generate_customer_id(self) -> str:
        """Generate a unique SecureWealth ID like SW3F8A21C9."""
        import secrets

        for _ in range(10):
            candidate = "SW" + secrets.token_hex(4).upper()
            if self.repo.get_user_by_customer_id(candidate) is None:
                return candidate
        raise RuntimeError("Could not allocate a unique customer ID.")

    # ── Configurable identifier resolution (task 2.2) ─────────────────────
    def _resolve_user(self, login_id: str):
        """
        Resolve the user via the configured LOGIN_METHODS
        (CUSTOMER_ID default; PHONE only if explicitly enabled).
        """
        from core.config import settings

        methods = [
            m.strip().upper()
            for m in settings.LOGIN_METHODS.split(",")
            if m.strip()
        ]
        for method in methods:
            if method == "CUSTOMER_ID":
                user = self.repo.get_user_by_customer_id(login_id)
            elif method == "PHONE":
                user = self.repo.get_user_by_phone(login_id)
            else:
                user = None
            if user is not None:
                return user
        return None
    
    # Register function that creates a new user and their credentials in the database
    def register(
        self,
        request: RegisterRequest,
    ):

        existing_user = self.repo.get_user_by_phone(
            request.phone
        )

        if existing_user:

            raise ValueError(
                "Phone number already registered."
            )

        try:

            user = User(

                user_id=uuid4(),

                customer_id=self._generate_customer_id(),

                full_name=request.full_name,

                phone=request.phone,

                email=request.email,

                date_of_birth=request.date_of_birth,

            )

            self.repo.create_user(user)

            credentials = AuthCredential(

                user_id=user.user_id,

                mpin_hash=hash_mpin(
                    request.mpin
                ),

            )

            self.repo.create_credentials(
                credentials
            )

            self.repo.db.commit()


            

            self.repo.db.refresh(user)

            return RegisterResponse(

                message=(
                    "Registration successful. Your SecureWealth ID is "
                    f"{user.customer_id} — you will need it to log in."
                ),

                user_id=user.user_id,

                customer_id=user.customer_id,

            )
        except Exception as e:

            self.repo.db.rollback()

            raise e

    
    # Login function that verifies the user's phone and MPIN, and returns a JWT access token if successful
    def login(
        self,
        request: LoginRequest,
    ) -> TokenResponse:

        user = self._resolve_user(request.login_id)

        if user is None:

            raise AuthenticationError(
                "Invalid SecureWealth ID or MPIN."
            )

        credentials = self.repo.get_credentials(
            user.user_id
        )

        if credentials is None:

            raise AuthenticationError(
                "Credentials not found."
            )

        if not verify_mpin(

            request.mpin,

            credentials.mpin_hash,

        ):

            self.repo.increment_failed_attempts(
                credentials
            )

            self.repo.db.commit()

            raise AuthenticationError(
                "Invalid SecureWealth ID or MPIN."
            )

        self.repo.reset_failed_attempts(
            credentials
        )

        self.repo.update_last_login(
            credentials
        )

        self.repo.db.commit()

        token = create_access_token(

            subject=str(
                user.user_id
            )

        )

        return TokenResponse(

            access_token=token

        )
    
    # Logout function that invalidates the user's session by updating the last login timestamp
    def logout(self):

        return LogoutResponse(
            message="Logged out successfully."
        )
    
    # Current Session
    def get_session(
        self,
        user: User,
    ):

        credentials = self.repo.get_credentials(
            user.user_id
        )

        return SessionResponse(
            user_id=user.user_id,
            full_name=user.full_name,
            customer_id=user.customer_id,
            phone=user.phone,
            email=user.email,
            last_login=credentials.last_login
        )