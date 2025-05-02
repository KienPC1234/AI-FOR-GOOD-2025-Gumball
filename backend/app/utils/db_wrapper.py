from typing import Optional, Any, List

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

import app.models as models
from app.extypes import UserRole
from app.models import PatientDetails, User, Scan, DoctorConnectToken


class AsyncDBWrapper:
    def __init__(self, session: AsyncSession):
        self.session = session

        # Short-circuiting the session methods
        self.commit = session.commit
        self.execute = session.execute
        self.close = session.close
        self.refresh = session.refresh
        self.add = session.add
        self.delete = session.delete # Add delete method

    # General save method

    async def save_model(self, model: 'Base'):
        """
        Save a model to the database.
        """
        self.add(model)
        await self.commit()
        await self.refresh(model)

    # User-related methods

    async def get_user(self, user_id: int) -> Optional[User]:
        """
        Fetch a user by ID.
        """
        return (await self.execute(select(User).filter(User.id == user_id))).scalar()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Fetch a user by email.
        """
        return (await self.execute(select(User).filter(User.email == email))).scalar()

    async def get_all_users(self, skip: int = 0, limit: int = 100, filters: List[Any] = None) -> List[User]:
        """
        Fetch all users with optional filters, pagination.
        """
        query = select(User)
        if filters:
            query = query.filter(*filters)
        return (await self.execute(query.offset(skip).limit(limit))).scalars().all()

    async def is_email_taken(self, email: str, exclude_user_id: Optional[int] = None) -> bool:
        """
        Check if an email is already taken, excluding a specific user ID.
        """
        query = select(User).filter(User.email == email)
        if exclude_user_id:
            query = query.filter(User.id != exclude_user_id)
        return (await self.execute(query)).scalar() is not None

    async def save_user(self, user: User) -> None:
        """
        Save a user to the database.
        """
        await self.save_model(user)

    async def soft_delete_user(self, user: User) -> None:
        """
        Soft delete a user by marking them as deleted and deactivating them.
        """
        await user.soft_delete()
        await self.save_user(user)

    async def restore_user(self, user: User) -> None:
        """
        Restore a soft-deleted user.
        """
        await user.soft_restore()
        await self.save_user(user)

    async def users(self, skip: int = 0, limit: int = 100, filters: Any = (), **kwargs) -> List[User]:
        """
        Query for users.
        """
        return (await self._command_query_users(skip, limit, filters, **kwargs)).scalars().all()

    async def user(self, *filters: Any, **kwargs) -> Optional[User]:
        """
        Query a user.
        """
        return (await self._command_query_users(limit=None, filters=filters, **kwargs)).scalar()

    async def _command_query_users(self, skip: int = 0, limit: Optional[int] = 100, filters: Any = (), **kwargs):
        query = select(User).offset(skip)
        compiled_filters = []

        if filters:
            compiled_filters.extend(filters)
        
        for col_name, value in kwargs.items():
            compiled_filters.append(getattr(User, col_name) == value)

        if limit:
            query = query.limit(limit)

        return await self.execute(query.filter(*compiled_filters))
    
    async def list_users(self, skip: int = 0, limit: Optional[int] = None, **kwargs):
        """
        Fetch users with optional filters and pagination. Ommit a rule if checking value is `None`
        """
        query = select(User).offset(skip)

        for col_name, value in kwargs.items():
            query = query.filter(getattr(User, col_name) == value)

        if limit:
            query = query.limit(limit)

        return (await self.execute(query)).scalars().all()


    # PatientDetails-related methods

    async def get_patient_details(self, patient_details_id: int) -> Optional[PatientDetails]: # Renamed method
        return (await self.execute(select(PatientDetails).filter(PatientDetails.id == patient_details_id))).scalar()

    
    async def get_patients_from_doctor_id(self, doctor_user_id: int, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Fetch all patient users associated with a specific doctor user.
        """
        
        doctor_user = await self.get_user(doctor_user_id)
        if not doctor_user or doctor_user.role != UserRole.DOCTOR:
            return []
        
        return await self.get_patient_for_doctor(doctor_user, skip, limit)
        
    async def get_patient_for_doctor(
        self,
        doctor: User,
        skip: int = 0,
        limit: int = 100,
    ) -> List[User]:
        return (await self.execute(
            select(User)
            .join(
                models.doctor_patient_association,
                User.id == models.doctor_patient_association.c.patient_user_id,
            )
            .filter(
                models.doctor_patient_association.c.doctor_user_id == doctor.id,
                User.role == UserRole.PATIENT,
                User.is_active == True,
            )
            .offset(skip)
            .limit(limit)
        )).scalars().all()

    async def get_doctors_from_patient_id(
        self, patient_user_id: int, skip: int = 0, limit: int = 100
    ) -> List[User]:
        """
        Fetch all patient users associated with a specific patient user.
        """
        
        patient = await self.get_user(patient_user_id)
        if not patient or patient.role != UserRole.PATIENT:
            return []

        return await self.get_doctors_for_patient(patient, skip, limit)

    async def get_doctors_for_patient(
        self, patient: User, skip: int = 0, limit: int = 100
    ) -> List[User]:
        
        return (await self.execute(
            select(User)
            .join(
                models.doctor_patient_association,
                User.id == models.doctor_patient_association.c.doctor_user_id,
            )
            .filter(
                models.doctor_patient_association.c.patient_user_id == patient.id,
                User.role == UserRole.DOCTOR,
                User.is_active.is_(True),
            )
            .offset(skip)
            .limit(limit)
        )).scalars().all()
        

    async def save_patient_details(self, patient_details: PatientDetails) -> None:
        await self.save_model(patient_details)

    async def update_patient_details(self, patient_details: PatientDetails) -> None:
        await self.commit()
        await self.refresh(patient_details)

    # Scan-related methods

    async def get_scan(self, scan_id: str) -> Optional[Scan]:
        """
        Fetch a scan by ID.
        """
        return (await self.execute(select(Scan).filter(Scan.id == scan_id))).scalar()

    async def get_scans_for_patient_user(self, patient_user_id: int, skip: int = 0, limit: int = 100) -> List[Scan]:
        """
        Fetch all scans for a specific patient user.
        """
        return (await self.execute(
            select(Scan)
            .filter(Scan.patient_user_id == patient_user_id)
            .offset(skip)
            .limit(limit)
        )).scalars().all()

    async def save_scan(self, scan: Scan) -> None:
        """
        Add a new scan to the database.
        """
        await self.save_model(scan)

    async def update_scan(self, scan: Scan) -> None:
        """
        Update an existing scan.
        """
        await self.commit()
        await self.refresh(scan)

    async def delete_scan(self, scan: Scan) -> None:
        """
        Delete a scan.
        """
        await self.delete(scan)
        await self.commit()

    # Token-related methods

    async def save_connect_token(self, token: DoctorConnectToken) -> None:
        """
        Add a new connection token to the database.
        """
        await self.save_model(token)

    async def get_connect_token(self, token: str) -> DoctorConnectToken:
        """
        Fetch a connection token by its value.
        """
        return (await self.execute(select(DoctorConnectToken).filter(DoctorConnectToken.token == token))).scalar()


class DBWrapper:
    def __init__(self, session: Session):
        self.session = session

        # Short-circuiting the session methods
        self.commit = session.commit
        self.query = session.query
        self.close = session.close
        self.refresh = session.refresh
        self.add = session.add
        self.delete = session.delete # Add delete method

    # General save method

    def save_model(self, model: 'Base'):
        """
        Save a model to the database.
        """
        self.add(model)
        self.commit()
        self.refresh(model)

    # User-related methods

    def get_user(self, user_id: int) -> Optional[User]:
        """
        Fetch a user by ID.
        """
        return self.query(User).filter(User.id == user_id).first()

    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Fetch a user by email.
        """
        return self.query(User).filter(User.email == email).first()

    def get_all_users(self, skip: int = 0, limit: int = 100, filters: List[Any] = None) -> List[User]:
        """
        Fetch all users with optional filters, pagination.
        """
        query = self.query(User)
        if filters:
            query = query.filter(*filters)
        return query.offset(skip).limit(limit).all()

    def is_email_taken(self, email: str, exclude_user_id: Optional[int] = None) -> bool:
        """
        Check if an email is already taken, excluding a specific user ID.
        """
        query = self.query(User).filter(User.email == email)
        if exclude_user_id:
            query = query.filter(User.id != exclude_user_id)
        return query.first() is not None

    def save_user(self, user: User) -> None:
        """
        Save a user to the database.
        """
        self.save_model(user)

    def soft_delete_user(self, user: User) -> None:
        """
        Soft delete a user by marking them as deleted and deactivating them.
        """
        user.soft_delete()
        self.save_user(user)

    def restore_user(self, user: User) -> None:
        """
        Restore a soft-deleted user.
        """
        user.soft_restore()
        self.save_user(user)

    def users(self, skip: int = 0, limit: int = 100, filters: Any = (), **kwargs) -> List[User]:
        """
        Query for users.
        """
        return self._command_query_users(skip, limit, filters, **kwargs).all()

    def user(self, *filters: Any, **kwargs) -> Optional[User]:
        """
        Query a user.
        """
        return self._command_query_users(limit=None, filters=filters, **kwargs).first()

    def _command_query_users(self, skip: int = 0, limit: Optional[int] = 100, filters: Any = (), **kwargs):
        query = self.query(User).offset(skip)
        compiled_filters = []

        if filters:
            compiled_filters.extend(filters)
        
        for col_name, value in kwargs.items():
            compiled_filters.append(getattr(User, col_name) == value)

        if limit:
            query = query.limit(limit)

        return query.filter(*compiled_filters)
    
    def list_users(self, skip: int = 0, limit: Optional[int] = None, **kwargs):
        """
        Fetch users with optional filters and pagination. Ommit a rule if checking value is `None`
        """
        query = self.query(User).offset(skip)

        for col_name, value in kwargs.items():
            query = query.filter(getattr(User, col_name) == value)

        if limit:
            query = query.limit(limit)

        return query.all()


    # PatientDetails-related methods

    def get_patient_details(self, patient_details_id: int) -> Optional[PatientDetails]: # Renamed method
        return self.query(PatientDetails).filter(PatientDetails.id == patient_details_id).first()

    
    def get_patients_from_doctor_id(self, doctor_user_id: int, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Fetch all patient users associated with a specific doctor user.
        """
        
        doctor_user = self.get_user(doctor_user_id)
        if not doctor_user or doctor_user.role != UserRole.DOCTOR:
            return []
        
        return self.get_patient_for_doctor(doctor_user, skip, limit)
        
    def get_patient_for_doctor(
        self,
        doctor: User,
        skip: int = 0,
        limit: int = 100,
    ) -> List[User]:
        return (
            self.query(User)
            .join(
                models.doctor_patient_association,
                User.id == models.doctor_patient_association.c.patient_user_id,
            )
            .filter(
                models.doctor_patient_association.c.doctor_user_id == doctor.id,
                User.role == UserRole.PATIENT,
                User.is_active == True,
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_doctors_from_patient_id(
        self, patient_user_id: int, skip: int = 0, limit: int = 100
    ) -> List[User]:
        """
        Fetch all patient users associated with a specific patient user.
        """
        
        patient = self.get_user(patient_user_id)
        if not patient or patient.role != UserRole.PATIENT:
            return []

        return self.get_doctors_for_patient(patient, skip, limit)

    def get_doctors_for_patient(
        self, patient: User, skip: int = 0, limit: int = 100
    ) -> List[User]:
        
        return (
            self.query(User)
            .join(
                models.doctor_patient_association,
                User.id == models.doctor_patient_association.c.doctor_user_id,
            )
            .filter(
                models.doctor_patient_association.c.patient_user_id == patient.id,
                User.role == UserRole.DOCTOR,
                User.is_active.is_(True),
            )
            .offset(skip)
            .limit(limit)
            .all()
        )
        

    def save_patient_details(self, patient_details: PatientDetails) -> None:
        self.save_model(patient_details)

    def update_patient_details(self, patient_details: PatientDetails) -> None:
        self.commit()
        self.refresh(patient_details)

    # Scan-related methods

    def get_scan(self, scan_id: str) -> Optional[Scan]:
        """
        Fetch a scan by ID.
        """
        return self.query(Scan).filter(Scan.id == scan_id).first()

    def get_scans_for_patient_user(self, patient_user_id: int, skip: int = 0, limit: int = 100) -> List[Scan]:
        """
        Fetch all scans for a specific patient user.
        """
        return (
            self.query(Scan)
            .filter(Scan.patient_user_id == patient_user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def save_scan(self, scan: Scan) -> None:
        """
        Add a new scan to the database.
        """
        self.save_model(scan)

    def update_scan(self, scan: Scan) -> None:
        """
        Update an existing scan.
        """
        self.commit()
        self.refresh(scan)

    def delete_scan(self, scan: Scan) -> None:
        """
        Delete a scan.
        """
        self.delete(scan)
        self.commit()

    # Token-related methods

    def save_connect_token(self, token: DoctorConnectToken) -> None:
        """
        Add a new connection token to the database.
        """
        self.save_model(token)

    def get_connect_token(self, token: str) -> DoctorConnectToken:
        """
        Fetch a connection token by its value.
        """
        return self.query(DoctorConnectToken).filter(DoctorConnectToken.token == token).first()