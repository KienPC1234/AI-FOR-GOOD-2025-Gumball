import os, json
from os import PathLike
from pathlib import Path
from typing import Callable, Any, Optional, List, Tuple

from celery import shared_task
from PIL import Image

from app.core.email import send_email
from app.core.storage import user_storage, Mounted
from app.models import User
from app.utils import change_ext, save_analyzation_output, load_analyzation_output
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
def convert_to_jpeg_task(user: User, img_name: str) -> str:
    """
    Converts an image to JPEG format.
    """
    file_mount = user_storage.user_uploaded_img_dir(user.id)

    try:
        img = Image.open(file_mount.read_file(img_name))
        
        jpeg_path = change_ext(img_name, ".jpeg")
        img.convert("L").save(jpeg_path, "JPEG")
        
        return jpeg_path
    except Exception as e:
        raise ImageProcessingError("Error converting image to JPEG") from e
    finally:
        file_mount.delete_file(img_name)
    

@shared_task
def analyze_xray_task(user: User, img_name: str):
    """
    Analyzes a grayscale X-ray image for pathologies then save details into a file.
    """
    try:
        img_path = user_storage.user_analyzed_img_dir(user.id).absolute_of(img_name)
        
        pathologies, gradcam_images = process_xray_image(img_path)
        save_path = user_storage.user_analysis_dir(user.id).avail_file_name(ext=".h5", absolute=True)

        # Will separate heatmap soon to optimize performance
        save_analyzation_output(save_path, pathologies, gradcam_images)
        return save_path.name
    except Exception as e:
        img_path.unlink()
        raise ImageProcessingError("Error analyzing X-ray image") from e


@shared_task
def expert_ai_xray_analysis_task(user: User, image_names: list[PathLike], symptoms: str):
    """
    Uses AI to provide suggestions based on X-ray analysis and symptoms.
    """
    try:
        user_dir = user_storage.user_dir(user.id)

        ai_expert = XrayAnalysisExpertAI()
        suggestions = ai_expert.analyze_xray(
            image_paths=tuple(map(user_dir.absolute_of, image_names)),
            symptoms=symptoms,
        )

        save_path = user_storage.user_analysis_dir(user.id).avail_file_name(ext=".json", absolute=True)
        with save_path.open("w") as fp:
            json.dump(suggestions, fp)

        return save_path.name
    except Exception as e:
        raise AITaskException("Error providing AI help") from e
    

@shared_task
def friendly_ai_xray_analysis_task(
    user_id: int, 
    analysis_name: str, 
    symptoms: Optional[str] = None
):
    """
    Uses AI to provide suggestions based on X-ray analysis and symptoms.
    """
    try:
        patient_ai = PatientAI()
        analysis_path = user_storage.user_analysis_dir(user_id).absolute_of(analysis_name)
        analysis = load_analyzation_output(analysis_path)

        suggestions = patient_ai.diagnose_images(
            processed_xrays=(analysis,),
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