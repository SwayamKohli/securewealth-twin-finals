from __future__ import annotations

import traceback
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.dependencies import get_current_user, get_db
from models.user import User
from schemas.device_schema import (
    DeviceResponse,
    RegisterDeviceRequest,
)
from schemas.user_schema import MessageResponse
from services.device_service import DeviceService

router = APIRouter(
    prefix="/api/v1/devices",
    tags=["Devices"],
)


@router.post(
    "/register",
    response_model=DeviceResponse,
)
def register_device(
    payload: RegisterDeviceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return DeviceService.register_device(
            db=db,
            user_id=current_user.user_id,
            payload=payload,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    except Exception:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register device.",
        )


@router.get(
    "",
    response_model=list[DeviceResponse],
)
def get_user_devices(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return DeviceService.get_devices(
            db=db,
            user_id=current_user.user_id,
        )

    except Exception:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch devices.",
        )


@router.get(
    "/current",
    response_model=DeviceResponse,
)
def get_current_device(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return DeviceService.get_current_device(
            db=db,
            user_id=current_user.user_id,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    except Exception:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch current device.",
        )


@router.delete(
    "/{device_id}",
    response_model=MessageResponse,
)
def delete_device(
    device_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        DeviceService.delete_device(
            db=db,
            user_id=current_user.user_id,
            device_id=device_id,
        )

        return MessageResponse(
            message="Device deactivated successfully.",
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    except Exception:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate device.",
        )