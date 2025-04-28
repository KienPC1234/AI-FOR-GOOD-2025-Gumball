# AFG_Gumball Module Documentation

## Overview
The `AFG_Gumball` module is a Python package designed for medical image processing and AI-assisted diagnosis, specifically for X-ray images. The module provides tools for X-ray image preprocessing, pathology detection, body part segmentation, and AI-assisted medical diagnosis using the Gemini AI backend. The module is divided into two submodules: `xray_processing` for image processing tasks and `medical_ai` for AI-based patient interaction and diagnosis functions.

### Module Structure
```
project/
├── AFG_Gumball/
│ ├── __init__.py
│ ├── __init__.pyi
│ ├── xray_processing/
│ │ ├── __init__.py
│ │ ├── image_loader.py
│ │ ├── gradcam.py
│ │ ├── segmentation.py
│ │ ├── model_utils.py
│ │ └── enums.py
│ ├── medical_ai/
│ │ ├── __init__.py
│ │ ├── gemini_client.py
│ │ ├── patient_ai.py
│ │ ├── doctor_diagnostic_ai.py
│ │ ├── doctor_enhance_ai.py
│ │ └── xray_analysis_expert_ai.py
```

- **`xray_processing`**: Handles X-ray image loading, preprocessing, pathology detection with Grad-CAM heatmaps, and body part segmentation.
- **`medical_ai`**: Provides AI-based functions for patient interaction, medical record creation, diagnosis validation, and advanced X-ray image analysis using the Gemini AI API.

## Installation

### Requirements
- Python 3.8 or higher
- Required libraries:
```bash
pip install torch torchvision numpy matplotlib scikit-image pillow python-dotenv google-generativeai>=0.8.0 torchxrayvision
```
- A valid Gemini API key stored in the `.env` file named `GEMINI_API_KEY`.

### Setup
1. Download or copy the `AFG_Gumball` module to your project directory.

2. Make sure the directory structure matches the structure above.
3. Create a `.env` file in the project root directory with the Gemini API key:
```
GEMINI_API_KEY=your_api_key_here
```
4. Install the dependent libraries:
```bash
pip install -r requirements.txt
```
(Create a `requirements.txt` file with the above libraries if needed.)
5. Run the scripts in the package context to ensure relative imports work:
```bash
python -m project.your_script
```

## Instructions

### 1. Submodule `xray_processing`
This submodule provides tools for X-ray image processing, including loading, pathology detection, Grad-CAM heatmap generation, and body part segmentation.

#### Main Components
- **Import**:
```python
from AFG_Gumball.xray_processing import load_xray_image, process_xray_image, compute_gradcam, get_body_part_segment, BodyPart
```

- **Functions**:
- `load_xray_image(image_input: Union[str, bytes]) -> torch.Tensor`: Load and preprocess X-ray images from file path or bytes data. Return tensor of size `[1, 512, 512]`.
- `process_xray_image(img_path: str) -> Tuple[List[Tuple[str, float]], List[Dict[str, Any]]]`: Process X-ray images to detect pathologies (probability > 0.5) and create Grad-CAM heatmaps. Returns a tuple containing a list of pathologies and a list of heatmap dictionaries.

- `compute_gradcam(model: torch.nn.Module, img_tensor: torch.Tensor, target_class_idx: int) -> np.ndarray`: Generates a Grad-CAM heatmap for a given pathology. Returns a combined image array.

- `get_body_part_segment(image: torch.Tensor, part: BodyPart) -> torch.Tensor`: Segments a given body part from an X-ray image using the PSPNet model. Returns a tensor of size `[512, 512]`.

- **Enum**:
- `BodyPart`: Enum for body parts (e.g. `LEFT_LUNG`, `HEART`, `SPINE`).

#### Example
```python
from AFG_Gumball.xray_processing import load_xray_image, process_xray_image, get_body_part_segment, BodyPart

# Load and preprocess X-ray images
image_tensor = load_xray_image("path/to/xray.jpg")

# Process images to detect pathologies
pathologies, gradcam_images = process_xray_image("path/to/xray.jpg")
for pathology, prob in pathologies:
  print(f"Pathology: {pathology}, Probability: {prob:.2f}")

# Heart segmentation
heart_segment = get_body_part_segment(image_tensor, BodyPart.HEART)
print(heart_segment.shape) # torch.Size([512, 512])
```

### 2. Submodule `medical_ai`
This submodule provides AI-based patient diagnostic and interaction tools, using the Gemini AI API for natural language processing and image analysis.

#### Main Components
- **Import**:
```python
from AFG_Gumball.medical_ai import GeminiAI, PatientAI, DoctorDiagnosticAI, DoctorEnhanceAI, XrayAnalysisExpertAI
```

- **Classes**:
- `GeminiAI`: Manages interactions with the Gemini AI API, including file uploads and content creation.
- `PatientAI`: Provides patient-friendly answers and diagnoses based on X-rays and symptoms.
- `DoctorDiagnosticAI`: Generates medical records, treatment suggestions, and inferences from symptoms for professional purposes.
- `DoctorEnhanceAI`: Improves medical records and validates diagnoses.
- `XrayAnalysisExpertAI`: Analyzes original X-ray images and symptoms, returning JSON results with diagnosis and abnormal areas.

#### Example: Load and analyze X-ray images
```python
from AFG_Gumball.medical_ai import PatientAI, XrayAnalysisExpertAI

# Load X-ray images
image_path = "path/to/xray.jpg"

# Patient-friendly diagnosis
patient_ai = PatientAI()
with open(image_path, "rb") as f:
  image_bytes = f.read()
  diagnosis, heatmaps = patient_ai.diagnose_images(
    image_bytes_list=[image_bytes],
    symptoms="Prolonged cough",
    include_symptoms=True,
    include_xray_image=True
  )
  print(f"Diagnosis: {diagnosis}")

# In-depth analysis
expert_ai = XrayAnalysisExpertAI()
result = expert_ai.analyze_xray(
  image_paths=[image_path],
  symptoms="Prolonged cough"
)
print(f"Analysis result: {result}")
```

#### Note when upload image
- **Image format**: X-ray images must be in JPEG format.
- **How ​​to upload images**:
- For `PatientAI.diagnose_images`:
```python
with open("path/to/xray.jpg", "rb") as f:
  image_bytes = f.read()
```
The `image_bytes` data is passed in as a list (`[image_bytes]`).
- For `DoctorDiagnosticAI.create_medical_record` and `XrayAnalysisExpertAI.analyze_xray`:
```python
image_paths = ["path/to/xray.jpg"]
```
- **Upload images to Gemini AI**:
- Use the file upload method to upload images first:
```python
import google.generativeai as genai
genai.configure(api_key="your_api_key")
response = genai.upload_file("path/to/xray.jpg", mime_type="image/jpeg")
file_uri = response.uri
```
- Pass the URI to `generate_content` with the correct structure:
```python
contents = [
{
  "role": "user",
  "parts": [
    {"file_data": {"file_uri": file_uri, "mime_type": "image/jpeg"}},
    {"text": "X-ray image analysis."}
  ]
}
]
model = genai.GenerativeModel("gemini-2.0-flash")
response = model.generate_content(contents)
```
- **Multiple image processing**: Methods that support image lists, up to 5 images.

### 3. Combining Submodules
The `medical_ai` submodule integrates with `xray_processing` to create comprehensive workflows. For example, `PatientAI` and `DoctorDiagnosticAI` use `process_xray_image` to analyze X-ray images before generating diagnoses or medical records.

#### Workflow example
```python
from AFG_Gumball.medical_ai import PatientAI, DoctorDiagnosticAI
from AFG_Gumball.xray_processing import process_xray_image

# X-ray image processing
pathologies, gradcam_images = process_xray_image("path/to/xray.jpg")

# Create medical record
doctor_ai = DoctorDiagnosticAI()
record = doctor_ai.create_medical_record(
  patient_info="Male, 50 years old",
  symptoms="Prolonged cough, shortness of breath",
  image_paths=["path/to/xray.jpg"],
  include_xray_image=True
)
print(f"Medical record: {record}")
```

## Note
- **Gemini API Key**: Make sure `GEMINI_API_KEY` is set in `.env` file to use the functions of `medical_ai`.

- **Image format**: X-ray images must be in JPEG format for processing in `PatientAI` and `XrayAnalysisExpertAI`. Use `PIL` to check and convert formats if necessary:
```python
from PIL import Image
img = Image.open("path/to/xray.png").convert("L")
img.save("xray.jpg", format="JPEG")
```
- **Library version**: Make sure to use `google-generativeai>=0.8.0` to support file uploads and format `contents` with `role`.

- **Contents format**: Each element in `contents` must have a `role` (`user` or `model`) and `parts` containing a list of `text` or `file_data`. For example:
```python
contents = [{"role": "user", "parts": [{"text": "Prompt"}]}]
```
- **Relative imports**: Run the script in the package context (e.g. `python -m project.your_script`) to avoid import errors.
- **Error handling**: All functions and methods include input checks and provide detailed error messages for invalid input.
