# API Documentation

## Authentication Endpoints (`/auth`)

### 1. Login (`POST /auth/login`)
Authenticate a user and obtain access/refresh tokens.

**Request Body (Form Data):**
```json
{
  "email": "string",
  "password": "string"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "access_token": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "refresh_token": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "token_type": "bearer"
  }
}
```

### 2. Register (`POST /auth/register`)
Register a new user in the system.

**Request Body:**
```json
{
  "email": "string",
  "password": "string",
  "role": "PATIENT|DOCTOR"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "email": "user@example.com",
    "is_active": true,
    "is_superuser": false,
    "role": "PATIENT",
    "id": 123,
    "created_at": "2025-05-08T10:00:00Z",
    "updated_at": "2025-05-08T10:00:00Z"
  }
}
```

### 3. Refresh Token (`POST /auth/refresh-token`)
Obtain a new access token using a refresh token.

**Request Headers:**
- `Authorization`: Bearer {refresh_token}

**Response (200):**
```json
{
  "success": true,
  "data": {
    "access_token": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "token_type": "bearer"
  }
}
```

---

## User Endpoints (users)

### 1. Get Current User (`GET /users/me`)
Retrieve the currently authenticated user's details.

**Response (200):**
```json
{
  "success": true,
  "data": {
    "email": "user@example.com",
    "is_active": true,
    "is_superuser": false,
    "role": "PATIENT",
    "id": 123,
    "created_at": "2025-05-08T10:00:00Z",
    "updated_at": "2025-05-08T10:00:00Z"
  }
}
```

### 2. Update Current User (`PUT /users/me`)
Update the current user's details.

**Request Body:**
```json
{
  "email": "string",
  "password": "string"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "email": "updated@example.com",
    "is_active": true,
    "role": "PATIENT",
    "id": 123
  }
}
```

### 3. List Users (`GET /users/`)
List all users (superuser only).

**Query Parameters:**
- `skip`: int (default: 0)
- `limit`: int (default: 100)
- `role`: string (optional)
- `is_active`: boolean (optional)

**Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "email": "user@example.com",
      "is_active": true,
      "role": "PATIENT",
      "id": 123
    }
  ]
}
```

---

## File Endpoints (`/files`)

### 1. Get Image (`GET /files/images/{scan_id}`)
Retrieve an image by scan ID.

**Parameters:**
- `scan_id`: string (path parameter)

**Response (200):**
- Content-Type: image/jpeg
- Body: Binary image data

**Error Responses:**
- 404: File not found
- 500: Failed to get image content

---

## Patient Endpoints (`/patients`)

### 1. Get Patients for Doctor (`GET /patients/`)
Retrieve all patients associated with the current doctor.

**Query Parameters:**
- `skip`: int (default: 0)
- `limit`: int (default: 100)

**Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "id": 123,
      "role": "PATIENT",
      "is_active": true
    }
  ]
}
```

### 2. Update Patient Details (`PUT /patients/{patient_user_id}`)
Update details for a specific patient.

**Parameters:**
- `patient_user_id`: int (path parameter)

**Request Body:**
```json
{
  "name": "string",
  "age": "integer",
  "gender": "string",
  "diagnosis": "string"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "name": "Jane Doe",
    "age": 36,
    "gender": "FEMALE",
    "diagnosis": "Updated diagnosis"
  }
}
```

### 3. Connect to Doctor (`POST /patients/connect-doctor/{connect_token}`)
Connect a patient to a doctor using a connection token.

**Parameters:**
- `connect_token`: string (path parameter)

**Response (200):**
```json
{
  "success": true,
  "data": {
    "id": 456,
    "role": "DOCTOR",
    "is_active": true,
    "email": "doctor@example.com"
  }
}
```

### 4. Create Connect Token (`POST /patients/create-connect-token`)
Create a token that patients can use to connect with a doctor.

**Request Body:**
```json
{
  "expires_in_minutes": 60
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "token": "550e8400-e29b-41d4-a716-446655440000",
    "expires_at": "2025-05-08T11:00:00Z",
    "doctor_id": 456
  }
}
```

All endpoints require authentication unless otherwise specified. Use the `Authorization` header with a Bearer token for authentication.

Common Error Responses:
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 422: Validation Error
- 500: Internal Server Error

# API Documentation (Continued)

## Scan Endpoints (`/scans`)

### 1. Upload Scan (`POST /scans/`)
Upload a new medical scan for analysis.

**Request Body (Multipart Form):**
- `file`: File (image)

**Response:**
```json
{
    "success": true,
    "data": {
        "scan_id": "550e8400-e29b-41d4-a716-446655440000",
        "task_token": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    }
}
```

### 2. Get Scan Details (`GET /scans/{scan_id}`)
Retrieve details of a specific scan.

**Path Parameters:**
- `scan_id`: integer

**Response:**
```json
{
    "success": true,
    "data": {
        "id": 123,
        "patient_id": 456,
        "scan_type": "XRAY",
        "status": "COMPLETED",
        "result": {
            "pathologies": ["pneumonia"],
            "confidence": 0.95
        },
        "created_at": "2025-05-08T10:00:00Z",
        "completed_at": "2025-05-08T10:05:00Z"
    }
}
```

---

## X-ray Analysis Endpoints (`/xray`)

### 1. Request Friendly Analysis (`POST /xray/friendly-analysis`)
Queue a friendly AI-powered analysis of an X-ray image.

**Request Body (Multipart Form):**
- `file`: File (X-ray image)
- `include_suggestions`: boolean (optional, default: true)

**Response:**
```json
{
    "success": true,
    "data": {
        "task_id": "550e8400-e29b-41d4-a716-446655440000",
        "estimated_time": "30 seconds"
    }
}
```

### 2. Request Expert Analysis (`POST /xray/expert-analysis`)
Queue an expert-level AI analysis of an X-ray image.

**Request Body (Multipart Form):**
- `file`: File (X-ray image)
- `additional_notes`: string (optional)
- `priority`: string (enum: "LOW", "MEDIUM", "HIGH")

**Response:**
```json
{
    "success": true,
    "data": {
        "task_id": "550e8400-e29b-41d4-a716-446655440000",
        "priority": "HIGH",
        "estimated_time": "2 minutes"
    }
}
```

### 3. Get Treatment Suggestions (`POST /xray/suggest-treatment`)
Get AI-powered treatment suggestions based on X-ray analysis.

**Request Body:**
```json
{
    "analysis_task_id": "string",
    "symptoms": "string",
    "patient_age": integer,
    "patient_gender": "string"
}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "suggestions": [
            {
                "condition": "string",
                "confidence": number,
                "treatment": "string",
                "precautions": "string"
            }
        ],
        "disclaimer": "string"
    }
}
```

---

## Task Management Endpoints (`/tasks`)

### 1. Get Task Status (`GET /tasks/status/{task_id}`)
Check the status of an asynchronous task.

**Path Parameters:**
- `task_id`: string

**Response:**
```json
{
    "success": true,
    "data": {
        "task_id": "550e8400-e29b-41d4-a716-446655440000",
        "status": "COMPLETED",
        "progress": 100,
        "result": {
            "type": "analysis",
            "data": {}
        }
    }
}
```

### 2. WebSocket Task Updates (`WebSocket /tasks/status/ws`)
Receive real-time updates about task progress.

**Connection Parameters:**
- `token`: string (Query parameter for authentication)
- `task_ids`: string (Comma-separated list of task IDs to monitor)

**WebSocket Messages:**
```json
{
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "IN_PROGRESS",
    "progress": 45,
    "message": "Processing image..."
}
```

### 3. Cancel Task (`POST /tasks/cancel/{task_id}`)
Cancel a running task.

**Path Parameters:**
- `task_id`: string

**Response:**
```json
{
    "success": true,
    "data": {
        "task_id": "550e8400-e29b-41d4-a716-446655440000",
        "status": "CANCELLED",
        "message": "Task cancelled successfully"
    }
}
```

### Common HTTP Status Codes

- `200`: Success
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden (insufficient permissions)
- `404`: Not Found
- `422`: Validation Error
- `500`: Internal Server Error

### Authentication

All endpoints require authentication via Bearer token in the Authorization header:
```
Authorization: Bearer <access_token>
```

### Rate Limiting

- Standard rate limit: 100 requests per minute
- WebSocket connections: 5 concurrent connections per user
- File upload size limit: 50MB per file

### Notes

1. All timestamps are in ISO 8601 format and UTC timezone
2. File uploads support JPEG, PNG, and DICOM formats
3. WebSocket connections will auto-disconnect after 30 minutes of inactivity