from typing import Collection


DEMO_SCAN_DATA = {
    "id": "xxxxxxxxxxxxxxxxxxxxxx",
    "type": "XRAY",
    "status": "ANALYZED",
    "patient_user_id": 123,
    "created_at": "2025-05-02T15:00:00Z",
    "updated_at": "2025-05-02T15:00:00Z",
}

DEMO_USER_DATA = {
    "email": "user@example.com",
    "is_active": True,
    "is_superuser": False,
    "role": "PATIENT",
    "id": 123,
    "created_at": "1900-01-01 01:01:01.1",
    "updated_at": "1900-01-01 01:01:01.1"
}

DEMO_USER_PUBLIC_DATA = {
    "id": 123,
    "role": "PATIENT",
    "is_active": True,
}

DEMO_PATIENT_DETAILS = {
    "name": "Jane Doe",
    "age": 36,
    "gender": "FEMALE",
    "diagnosis": "Updated diagnosis"
}

def DEMO_RESPONSE(data: dict, success: bool = True):
    return {
        "success": success,
        "data": data
    }