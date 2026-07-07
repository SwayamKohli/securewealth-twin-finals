from __future__ import annotations

import traceback
from uuid import UUID

from sqlalchemy.orm import Session

from models.device import Device


class DeviceRepository:

    @staticmethod
    def create(
        db: Session,
        device: Device,
    ) -> Device:
        try:
            db.add(device)
            db.commit()
            db.refresh(device)

            return device

        except Exception:
            db.rollback()
            traceback.print_exc()
            raise

    @staticmethod
    def get_by_id(
        db: Session,
        device_id: UUID,
    ) -> Device | None:
        try:
            return (
                db.query(Device)
                .filter(Device.device_id == device_id)
                .first()
            )
        except Exception:
            traceback.print_exc()
            raise

    @staticmethod
    def get_user_devices(
        db: Session,
        user_id: UUID,
    ) -> list[Device]:
        try:
            return (
                db.query(Device)
                .filter(
                    Device.user_id == user_id,
                    Device.is_active.is_(True),
                )
                .all()
            )
        except Exception:
            traceback.print_exc()
            raise

    @staticmethod
    def get_current_device(
        db: Session,
        user_id: UUID,
    ) -> Device | None:
        try:
            return (
                db.query(Device)
                .filter(
                    Device.user_id == user_id,
                    Device.is_active.is_(True),
                )
                .order_by(Device.last_seen.desc())
                .first()
            )
        except Exception:
            traceback.print_exc()
            raise

    @staticmethod
    def deactivate(
        db: Session,
        device: Device,
    ) -> Device:
        try:
            device.is_active = False

            db.commit()
            db.refresh(device)

            return device

        except Exception:
            db.rollback()
            traceback.print_exc()
            raise