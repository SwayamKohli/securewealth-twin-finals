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
            print("Committed!")

            found = self.repo.get_user_by_phone(request.phone)

            print(found)
            

            self.repo.db.refresh(user)

            return RegisterResponse(

                message="Registration successful.",

                user_id=user.user_id,

            )
        except Exception as e:

            self.repo.db.rollback()

            raise e

    
    # Login function that verifies the user's phone and MPIN, and returns a JWT access token if successful
    def login(
        self,
        request: LoginRequest,
    ) -> TokenResponse:

        user = self.repo.get_user_by_phone(
            request.phone
        )

        if user is None:

            raise ValueError(
                "Invalid phone or MPIN."
            )

        credentials = self.repo.get_credentials(
            user.user_id
        )

        if credentials is None:

            raise ValueError(
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

            raise ValueError(
                "Invalid phone or MPIN."
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
            phone=user.phone,
            email=user.email,
            last_login=credentials.last_login
        )