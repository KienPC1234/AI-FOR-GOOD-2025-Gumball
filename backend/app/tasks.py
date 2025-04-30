import os
from os import PathLike
from pathlib import Path
from typing import Callable, Any, Optional, List, Tuple
from PIL import Image

from celery import shared_task

from app.core.email import send_email
from app.core.storage import user_storage, Mounted
from app.utils import change_ext
from app.states import ImageProcessingError, AITaskException
from ...AFG_Gumball.xray_processing import process_xray_image
from ...AFG_Gumball.medical_ai import XrayAnalysisExpertAI, PatientAI, DoctorDiagnosticAI, DoctorEnhanceAI


###################################################
# NOTE: Tasks should only return intermediate link.
# Execution result will be save to disk.
# This is to prevent security flaws.
###################################################


"""
Current implementation plan:
+ convert_to_jpeg_task
+ analyze_xray_task
+ friendly_ai_xray_analysis_task
+ create_medical_record_task
"""


@shared_task
def send_email_task(email_to: str, subject: str, html_content: str) -> None:
    send_email(email_to=email_to, subject=subject, html_content=html_content)
    

@shared_task
def convert_to_jpeg_task(user_id: int, file_name: str) -> str:
    """
    Converts an image to JPEG format.
    """
    file_mount = user_storage.user_dir(user_id)

    try:
        with file_mount.cd(user_storage.RAW_IMG_DIR):
            img = Image.open(file_mount.read_file(file_name))
        
        with file_mount.cd(user_storage.JPEG_IMG_DIR):
            jpeg_path = change_ext(file_name, ".jpeg")
            img.convert("L").save(jpeg_path, "JPEG")
        
        return jpeg_path
    except Exception as e:
        raise ImageProcessingError("Error converting image to JPEG") from e
    finally:
        file_mount.delete_file(user_storage.RAW_IMG_DIR / file_name)
    

@shared_task
def analyze_xray_task(img_path: str):
    """
    Analyzes a grayscale X-ray image for pathologies.
    """
    try:
        pathologies, gradcam_images = process_xray_image(img_path)
        return {
            "pathologies": pathologies,
            "gradcam_images": gradcam_images,
        }
    except Exception as e:
        raise ImageProcessingError("Error analyzing X-ray image") from e


@shared_task
def expert_ai_xray_analysis_task(analysis_result: dict, symptoms: str):
    """
    Uses AI to provide suggestions based on X-ray analysis and symptoms.
    """
    try:
        ai_expert = XrayAnalysisExpertAI()
        suggestions = ai_expert.analyze_xray(
            image_paths=[gradcam["heatmap"] for gradcam in analysis_result["gradcam_images"]],
            symptoms=symptoms,
        )
        return suggestions
    except Exception as e:
        raise AITaskException("Error providing AI help") from e
    

@shared_task
def friendly_ai_xray_analysis_task(user_id: int, xray_image: Optional[PathLike] = None, symptoms: Optional[str] = None):
    """
    Uses AI to provide suggestions based on X-ray analysis and symptoms.
    """
    try:
        patient_ai = PatientAI()
        xray_image = user_storage.user_dir(user_id).absolute_of(xray_image).read_bytes()

        suggestions = patient_ai.diagnose_images(
            image_paths=[xray_image],
            symptoms=symptoms,
            include_xray_image=False, # We don't want to comsume to much computational power :))
        )
        return suggestions
    except Exception as e:
        raise AITaskException("Error providing AI help") from e


@shared_task
def create_medical_record_task(
    user_id: int,
    patient_info: str,
    symptoms: str,
    image_paths: list[PathLike],
    include_xray_image: bool = False,
) -> dict:
    """
    Creates a medical record based on the provided information and images.
    """
    try:
        patient_ai = DoctorDiagnosticAI()
        image_paths = [user_storage.user_dir(user_id).absolute_of(image_path) for image_path in image_paths]
        medical_record = patient_ai.create_medical_record(
            patient_info=patient_info,
            symptoms=symptoms,
            image_paths=image_paths,
            include_xray_image=include_xray_image,
        )
        return medical_record
    except Exception as e:
        raise AITaskException("Error creating medical record") from e


@shared_task
def validate_diagnosis_task(
    symptoms: str,
    pathologies_list: List[List[Tuple[str, float]]],
    medical_record: str
):
    """
    Validates a medical record based on the provided information.
    """
    try:
        enhance_ai = DoctorEnhanceAI()
        return enhance_ai.validate_diagnosis(
            symptoms,
            pathologies_list,
            medical_record
        )
    except Exception as e:
        raise AITaskException("Error validating medical record") from e
    

@shared_task
def enhance_medical_record_task(medical_record: str):
    """
    Enhance a medical record.
    """
    try:
        enhance_ai = DoctorEnhanceAI()
        return enhance_ai.enhance_medical_record(
            medical_record
        )
    except Exception as e:
        raise AITaskException("Error enhancing medical record") from e