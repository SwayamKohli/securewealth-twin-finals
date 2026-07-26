from __future__ import annotations

import traceback
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from database.repositories.device_repository import DeviceRepository
from models.device import Device
from models.enums import TrustStatus
from schemas.device_schema import RegisterDeviceRequest


class DeviceService:

    @staticmethod
    def register_device(
        db: Session,
        user_id: UUID,
        payload: RegisterDeviceRequest,
    ) -> Device:
        try:
            device = Device(
                user_id=user_id,
                device_name=payload.device_name,
                device_type=payload.device_type,
                sim_id=payload.sim_id,
                trust_status=TrustStatus.TRUSTED,
                first_seen=datetime.now(timezone.utc),
                last_seen=datetime.now(timezone.utc),
                is_active=True,
            )

            return DeviceRepository.create(
                db=db,
                device=device,
            )

        except Exception:
            traceback.print_exc()
            raise

    @staticmethod
    def get_devices(
        db: Session,
        user_id: UUID,
    ) -> list[Device]:
        try:
            return DeviceRepository.get_user_devices(
                db=db,
                user_id=user_id,
            )

        except Exception:
            traceback.print_exc()
            raise

    @staticmethod
    def get_current_device(
        db: Session,
        user_id: UUID,
    ) -> Device:
        try:
            device = DeviceRepository.get_current_device(
                db=db,
                user_id=user_id,
            )

            if not device:
                raise ValueError("No active device found.")

            return device

        except Exception:
            traceback.print_exc()
            raise

    @staticmethod
    def delete_device(
        db: Session,
        user_id: UUID,
        device_id: UUID,
    ) -> Device:
        try:
            device = DeviceRepository.get_by_id(
                db=db,
                device_id=device_id,
            )

            if not device:
                raise ValueError("Device not found.")

            if device.user_id != user_id:
                raise ValueError("Unauthorized device access.")

            if not device.is_active:
                raise ValueError("Device already deactivated.")

            return DeviceRepository.deactivate(
                db=db,
                device=device,
            )

        except Exception:
            traceback.print_exc()
            raise