from enum import IntEnum
from sqlalchemy.types import TypeDecorator, Integer

__all__ = 'UserRole', 'IntEnumType'

class UserRole(IntEnum):
    """
    User role in the application, not the permission level. 
    """

    PATIENT = 0
    DOCTOR = 1
    # MANAGER = 2 # for hospital manager
    

class IntEnumType(TypeDecorator):
    impl = Integer

    def __init__(self, enumtype, *args, **kwargs):
        super(IntEnumType, self).__init__(*args, **kwargs)
        self._enumtype = enumtype

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return value.value if isinstance(value, self._enumtype) else int(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return self._enumtype(value)
