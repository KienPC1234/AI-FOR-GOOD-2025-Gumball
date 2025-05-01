Documentation for endpoints:

---

## **Authentication Endpoints (`/auth`)**

### **1. `/auth/register`**
- **Method**: `POST`
- **Description**: Registers a new user.
- **Parameters**:
  - `email` (string): User's email.
  - `password` (string): User's password.
  - `role` (string): User's role (`PATIENT`, `DOCTOR`).
- **Response**: User object.
- **Example**:
  ```bash
  curl -X POST "http://localhost:8000/api/auth/register" -d '{"email": "user@example.com", "password": "pass", "role": "PATIENT"}'
  ```

### **2. `/auth/login`**
- **Method**: `POST`
- **Description**: Logs in a user and returns tokens.
- **Parameters**:
  - `email` (string): User's email.
  - `password` (string): User's password.
- **Response**: Access and refresh tokens.
- **Example**:
  ```bash
  curl -X POST "http://localhost:8000/api/auth/login" -d '{"email": "user@example.com", "password": "pass"}'
  ```

### **3. `/auth/refresh-token`**
- **Method**: `POST`
- **Description**: Refreshes the access token.
- **Parameters**:
  - `refresh_token` (string): Refresh token.
- **Response**: New access token.
- **Example**:
  ```bash
  curl -X POST "http://localhost:8000/api/auth/refresh-token" -H "Authorization: Bearer <refresh_token>"
  ```

---

## **User Endpoints (users)**

### **1. `/users/me`**
- **Method**: `GET`
- **Description**: Retrieves the current user's details.
- **Response**: User object.
- **Example**:
  ```bash
  curl -X GET "http://localhost:8000/api/users/me" -H "Authorization: Bearer <access_token>"
  ```

### **2. users**
- **Method**: `GET`
- **Description**: Retrieves a list of users (superuser only).
- **Parameters**:
  - `skip` (int): Records to skip.
  - `limit` (int): Max records to return.
  - `role` (string): Filter by role.
  - `is_active` (bool): Filter by active status.
- **Response**: List of users.
- **Example**:
  ```bash
  curl -X GET "http://localhost:8000/api/users/?role=DOCTOR" -H "Authorization: Bearer <access_token>"
  ```

---

## **Patient Endpoints (`/patients`)**

### **1. `/patients/`**
- **Method**: `GET`
- **Description**: Retrieves patients associated with the current doctor.
- **Parameters**:
  - `skip` (int): Records to skip.
  - `limit` (int): Max records to return.
- **Response**: List of patients.
- **Example**:
  ```bash
  curl -X GET "http://localhost:8000/api/patients/" -H "Authorization: Bearer <access_token>"
  ```

### **2. `/patients/connect-doctor/{connect_token}`**
- **Method**: `POST`
- **Description**: Connects a patient to a doctor using a token.
- **Parameters**:
  - `connect_token` (string): Token for connection.
- **Response**: Doctor object.
- **Example**:
  ```bash
  curl -X POST "http://localhost:8000/api/patients/connect-doctor/<connect_token>" -H "Authorization: Bearer <access_token>"
  ```

---

## **File Endpoints (`/files`)**

### **1. `/files/images`**
- **Method**: `POST`
- **Description**: Uploads an image for processing.
- **Parameters**:
  - `file` (file): Image file.
- **Response**: Task ID for processing.
- **Example**:
  ```bash
  curl -X POST "http://localhost:8000/api/files/images" -F "file=@image.jpg" -H "Authorization: Bearer <access_token>"
  ```

### **2. `/files/images/{file_name}`**
- **Method**: `GET`
- **Description**: Retrieves a processed image.
- **Parameters**:
  - `file_name` (string): Name of the file.
- **Response**: Image file.
- **Example**:
  ```bash
  curl -X GET "http://localhost:8000/api/files/images/example.jpg" -H "Authorization: Bearer <access_token>"
  ```

---

## **X-ray Endpoints (`/xray`)**

### **1. `/xray/friendly-analysis`**
- **Method**: `POST`
- **Description**: Provides treatment suggestions using a friendly AI model.
- **Parameters**:
  - `task_id` (string): X-ray analysis task ID.
  - `symptoms` (string): User symptoms.
- **Response**: Task ID for suggestions.
- **Example**:
  ```bash
  curl -X POST "http://localhost:8000/api/xray/friendly-analysis" -d '{"task_id": "abc123", "symptoms": "cough"}' -H "Authorization: Bearer <access_token>"
  ```

### **2. `/xray/expert-analysis`**
- **Method**: `POST`
- **Description**: Provides treatment suggestions using an expert AI model.
- **Parameters**:
  - `task_id` (string): X-ray analysis task ID.
  - `symptoms` (string): User symptoms.
- **Response**: Task ID for suggestions.
- **Example**:
  ```bash
  curl -X POST "http://localhost:8000/api/xray/expert-analysis" -d '{"task_id": "abc123", "symptoms": "fever"}' -H "Authorization: Bearer <access_token>"
  ```

---

## **Task Endpoints (`/tasks`)**

### **1. `/tasks/status/`**
- **Method**: `GET`
- **Description**: Retrieves the status of a Celery task.
- **Response**: Task status and result.
- **Example**:
  ```bash
  curl -X GET "http://localhost:8000/api/tasks/status/" -H "Authorization: Bearer <access_token>"
  ```

---

## **Scan Endpoints (`/scans`)**

### **1. `/scans/`**
- **Method**: `POST`
- **Description**: Creates a new scan for the current patient.
- **Parameters**:
  - `scan_type` (string): Type of scan.
  - `image_path` (string): Path to the image.
  - `status` (string): Scan status.
- **Response**: Scan object.
- **Example**:
  ```bash
  curl -X POST "http://localhost:8000/api/scans/" -d '{"scan_type": "X-ray", "image_path": "/path/to/image", "status": "pending"}' -H "Authorization: Bearer <access_token>"
  ```

### **2. `/scans/{scan_id}`**
- **Method**: `GET`
- **Description**: Retrieves a specific scan by ID.
- **Parameters**:
  - `scan_id` (int): ID of the scan.
- **Response**: Scan object.
- **Example**:
  ```bash
  curl -X GET "http://localhost:8000/api/scans/1" -H "Authorization: Bearer <access_token>"
  ```