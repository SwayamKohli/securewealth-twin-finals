from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.dependencies import (
    get_current_user,
    get_db,
)

from core.exceptions import (
    AuthenticationError,
    UserAlreadyExistsError,
)

from models.user import User

from schemas.auth_schema import (
    LoginRequest,
    LogoutResponse,
    RegisterRequest,
    RegisterResponse,
    SessionResponse,
    TokenResponse,
)

from services.auth_service import AuthService


router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"],
)


@router.post(

    "/register",

    response_model=RegisterResponse,

    status_code=status.HTTP_201_CREATED,

)
def register(

    request: RegisterRequest,

    db: Session = Depends(get_db),

):

    service = AuthService(db)

    # try:

    #     return service.register(request)

    # except UserAlreadyExistsError as exc:

    #     raise HTTPException(

    #         status_code=status.HTTP_409_CONFLICT,

    #         detail=str(exc),

    #     )
    try:
        return service.register(request)

    except Exception as e:
        print("=" * 80)
        print("REGISTER ENDPOINT ERROR")
        print(type(e).__name__)
        print(e)
        print("=" * 80)
        raise
    
@router.post(

    "/login",

    response_model=TokenResponse,

)
def login(

    request: LoginRequest,

    db: Session = Depends(get_db),

):

    service = AuthService(db)

    try:

        return service.login(request)

    except AuthenticationError as exc:

        raise HTTPException(

            status_code=status.HTTP_401_UNAUTHORIZED,

            detail=str(exc),

        )

@router.post(

    "/logout",

    response_model=LogoutResponse,

)
def logout(

    db: Session = Depends(get_db),

):

    service = AuthService(db)

    return service.logout()


@router.get(

    "/session",

    response_model=SessionResponse,

)
def current_session(

    current_user: User = Depends(

        get_current_user

    ),

    db: Session = Depends(

        get_db

    ),

):

    service = AuthService(db)

    return service.get_session(

        current_user

    )
