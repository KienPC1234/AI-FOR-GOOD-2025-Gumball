import os, json
from os import PathLike
from pathlib import Path
from typing import Callable, Any, Optional, List, Tuple

from celery import shared_task
from PIL import Image

from app.core.email import send_email
from app.core.storage import user_storage
from app.extypes import ImageProcessingError, AITaskException, AIInspectionType
from app.models import User
from app.utils import change_ext, save_analyzation_output, load_analyzation_output
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
    

@shared_task(name="app.tasks.convert_to_jpeg")
def convert_to_jpeg_task(user: User, img_name: str) -> str:
    """
    Converts an image to JPEG format.
    """
    user_dir = user_storage.dir_of(user.id)
    img_path = user_dir.uploaded_image(img_name)
    scan_id = os.path.splitext(img_path.name)[1]

    try:
        img = Image.open(img_path)
        
        jpeg_path = change_ext(img_path, ".jpeg")
        img.convert("L").save(jpeg_path, "JPEG")
        
        return scan_id
    except Exception as e:
        raise ImageProcessingError("Error converting image to JPEG") from e
    finally:
        img_path.unlink(missing_ok=True)
    

@shared_task(name="app.tasks.analyze_xray")
def analyze_xray_task(user: User, scan_id: str):
    """
    Analyzes a grayscale X-ray image for pathologies then save details into a file.
    """
    user_folder = user_storage.dir_of(user.id)

    try:
        img_path = user_folder.analyzed_image(scan_id)
        
        pathologies, gradcam_images = process_xray_image(img_path)
        save_path = user_folder.new_analysis_name(scan_id)

        # Will separate heatmap soon to optimize performance
        save_analyzation_output(save_path, pathologies, gradcam_images)
        return scan_id
    except Exception as e:
        img_path.unlink() # Remove image if errored
        raise ImageProcessingError("Error analyzing X-ray image") from e


@shared_task(name="app.tasks.expert_analysis")
def expert_ai_xray_analysis_task(
    user: User,
    scan_id: str,
    symptoms: str
):
    """
    Uses AI to provide suggestions based on X-ray analysis and symptoms.
    """
    try:
        user_folder = user_storage.dir_of(user.id)
        save_path = user_folder.new_inspection_name(scan_id, AIInspectionType.EXPERT)

        ai_expert = XrayAnalysisExpertAI()
        suggestions = ai_expert.analyze_xray(
            image_paths=(user_folder.analyzed_image(scan_id),),
            symptoms=symptoms,
        )

        with save_path.open("w") as fp:
            json.dump(suggestions, fp)

        return scan_id
    except Exception as e:
        raise AITaskException("Error providing AI help") from e
    

@shared_task(name="app.tasks.friendly_analysis")
def friendly_ai_xray_analysis_task(
    user: User, 
    scan_id: str, 
    symptoms: Optional[str] = None
):
    """
    Uses AI to provide suggestions based on X-ray analysis and symptoms.
    """
    user_folder = user_storage.dir_of(user.id)
    try:
        save_path = user_folder.new_inspection_name(scan_id, AIInspectionType.FRIENDLY)
        analysis = user_folder.read_analysis(scan_id)

        patient_ai = PatientAI()
        suggestions = patient_ai.diagnose_images(
            processed_xrays=(analysis,),
            symptoms=symptoms,
            include_xray_image=False, # We don't want to comsume to much computational power :))
        )

        save_path.write_text(suggestions)

        return scan_id
    except Exception as e:
        raise AITaskException("Error providing AI help") from e


# @shared_task
# def create_medical_record_task(
#     user_id: int,
#     patient_info: str,
#     symptoms: str,
#     image_paths: list[PathLike],
#     include_xray_image: bool = False,
# ) -> dict:
#     """
#     Creates a medical record based on the provided information and images.
#     """
#     try:
#         patient_ai = DoctorDiagnosticAI()
#         image_paths = [user_storage.user_dir(user_id).abs_of(image_path) for image_path in image_paths]
#         medical_record = patient_ai.create_medical_record(
#             patient_info=patient_info,
#             symptoms=symptoms,
#             image_paths=image_paths,
#             include_xray_image=include_xray_image,
#         )
#         return medical_record
#     except Exception as e:
#         raise AITaskException("Error creating medical record") from e


# @shared_task
# def validate_diagnosis_task(
#     symptoms: str,
#     pathologies_list: List[List[Tuple[str, float]]],
#     medical_record: str
# ):
#     """
#     Validates a medical record based on the provided information.
#     """
#     try:
#         enhance_ai = DoctorEnhanceAI()
#         return enhance_ai.validate_diagnosis(
#             symptoms,
#             pathologies_list,
#             medical_record
#         )
#     except Exception as e:
#         raise AITaskException("Error validating medical record") from e
    

# @shared_task
# def enhance_medical_record_task(medical_record: str):
#     """
#     Enhance a medical record.
#     """
#     try:
#         enhance_ai = DoctorEnhanceAI()
#         return enhance_ai.enhance_medical_record(
#             medical_record
#         )
#     except Exception as e:
#         raise AITaskException("Error enhancing medical record") from e