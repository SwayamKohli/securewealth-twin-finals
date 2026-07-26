# backend/database/repositories/behavioural_profile_repository.py
from __future__ import annotations

import traceback
from uuid import UUID

from sqlalchemy.orm import Session

from models.behavioural_profile import BehaviouralProfile


class BehaviouralProfileRepository:

    @staticmethod
    def get_by_user_id(
        db: Session,
        user_id: UUID,
    ) -> BehaviouralProfile | None:
        try:
            return (
                db.query(BehaviouralProfile)
                .filter(BehaviouralProfile.user_id == user_id)
                .first()
            )
        except Exception:
            traceback.print_exc()
            raise

    @staticmethod
    def create(
        db: Session,
        profile: BehaviouralProfile,
    ) -> BehaviouralProfile:
        try:
            db.add(profile)
            db.commit()
            db.refresh(profile)
            return profile
        except Exception:
            db.rollback()
            traceback.print_exc()
            raise

    @staticmethod
    def update(
        db: Session,
        profile: BehaviouralProfile,
    ) -> BehaviouralProfile:
        try:
            db.commit()
            db.refresh(profile)
            return profile
        except Exception:
            db.rollback()
            traceback.print_exc()
            raise