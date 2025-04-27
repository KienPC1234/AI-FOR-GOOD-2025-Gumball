import os
from .gemini_client import GeminiAI
from ..xray_processing import process_xray_image
import google.generativeai as genai


class DoctorDiagnosticAI:
    def __init__(self):
        self.gemini = GeminiAI()
        self.max_images = 5

    def process_xray_image(self, img_path: str) -> tuple[list[tuple[str, float]], list[dict]]:
        if not os.path.exists(img_path):
            raise ValueError(f"Đường dẫn ảnh {img_path} không tồn tại")
        return process_xray_image(img_path)

    def create_medical_record(
        self,
        patient_info: str,
        symptoms: str,
        image_paths: list[str],
        include_xray_image: bool = False
    ) -> str:
        if not isinstance(patient_info, str) or not patient_info.strip():
            raise ValueError("Thông tin bệnh nhân phải là chuỗi không rỗng")
        if not isinstance(symptoms, str) or not symptoms.strip():
            raise ValueError("Triệu chứng phải là chuỗi không rỗng")
        if not image_paths or len(image_paths) > self.max_images:
            raise ValueError(f"Số lượng ảnh phải từ 1 đến {self.max_images}")

        pathologies_list = []
        gradcam_images_list = []
        for img_path in image_paths:
            if not os.path.exists(img_path):
                raise ValueError(f"Đường dẫn ảnh {img_path} không tồn tại")
            pathologies, gradcam_images = self.process_xray_image(img_path)
            pathologies_list.append(pathologies)
            gradcam_images_list.append(gradcam_images)
        
        prompt = """
        Bạn là một AI y tế chuyên nghiệp hỗ trợ bác sĩ. Dựa trên thông tin bệnh nhân, triệu chứng, kết quả phân tích ảnh X-quang và ảnh X-quang gốc (nếu có), tạo một bệnh án chi tiết theo các bước:
        1. Ghi nhận thông tin bệnh nhân.
        2. Liệt kê triệu chứng.
        3. Phân tích kết quả ảnh X-quang.
        4. Nếu có ảnh X-quang gốc, phân tích trực tiếp để bổ sung thông tin.
        5. Đưa ra chẩn đoán sơ bộ.
        6. Đề xuất gợi ý điều trị.
        Sử dụng ngôn ngữ y khoa chính xác, chuyên nghiệp.

        Ví dụ:
        Thông tin bệnh nhân: Nam, 50 tuổi, tiền sử hút thuốc.
        Triệu chứng: Ho kéo dài, khó thở.
        Kết quả ảnh X-quang: Ảnh 1: Viêm phổi (Xác suất 0.75).
        Bệnh án:
        - Thông tin bệnh nhân: Nam, 50 tuổi, tiền sử hút thuốc 30 năm.
        - Triệu chứng: Ho kéo dài 2 tháng, khó thở khi gắng sức.
        - Kết quả phân tích: Viêm phổi với xác suất 0.75 trên ảnh X-quang.
        - Chẩn đoán sơ bộ: Viêm phổi cấp.
        - Gợi ý điều trị: Kháng sinh (Amoxicillin 500mg, 3 lần/ngày), theo dõi SpO2, chụp X-quang lại sau 7 ngày.

        Thông tin bệnh nhân: {patient_info}
        Triệu chứng: {symptoms}
        Kết quả phân tích ảnh X-quang:
        """
        for i, (pathologies, gradcam) in enumerate(zip(pathologies_list, gradcam_images_list)):
            prompt += f"\nẢnh {i+1}:\n"
            for pathology, prob in pathologies:
                prompt += f"- {pathology}: Xác suất {prob:.2f}\n"
        
        prompt = prompt.format(patient_info=patient_info, symptoms=symptoms)

        contents = []
        if include_xray_image:
            for i, img_path in enumerate(image_paths):
                try:
                    file_uri = self.gemini.upload_file(img_path)
                    contents.append({
                        "role": "user",
                        "parts": [
                            {"file_data": {"file_uri": file_uri, "mime_type": "image/jpeg"}},
                            {"text": f"Phân tích ảnh X-quang {i+1} cùng với kết quả trên."}
                        ]
                    })
                except Exception as e:
                    raise RuntimeError(f"Lỗi khi tải ảnh lên: {str(e)}")
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        return self.gemini.generate_content(contents)

    def suggest_treatment(self, symptoms: str, pathologies_list: list[list[tuple[str, float]]]) -> str:
        if not isinstance(symptoms, str) or not symptoms.strip():
            raise ValueError("Triệu chứng phải là chuỗi không rỗng")
        if not pathologies_list:
            raise ValueError("Danh sách bệnh lý không được rỗng")

        prompt = """
        Bạn là một AI y tế hỗ trợ bác sĩ. Dựa trên triệu chứng và kết quả phân tích ảnh X-quang, đưa ra gợi ý điều trị chuyên sâu theo các bước:
        1. Xác định bệnh lý chính dựa trên triệu chứng và kết quả X-quang.
        2. Đề xuất thuốc hoặc liệu pháp phù hợp.
        3. Gợi ý xét nghiệm bổ sung nếu cần.
        4. Cung cấp lời khuyên theo dõi.
        Sử dụng ngôn ngữ y khoa chuyên nghiệp.

        Triệu chứng: {symptoms}
        Kết quả phân tích ảnh X-quang:
        """
        for i, pathologies in enumerate(pathologies_list):
            prompt += f"\nẢnh {i+1}:\n"
            for pathology, prob in pathologies:
                prompt += f"- {pathology}: Xác suất {prob:.2f}\n"
        
        prompt = prompt.format(symptoms=symptoms)
        contents = [{"role": "user", "parts": [{"text": prompt}]}]
        return self.gemini.generate_content(contents)

    def reason_from_symptoms(self, symptoms: str) -> str:
        if not isinstance(symptoms, str) or not symptoms.strip():
            raise ValueError("Triệu chứng phải là chuỗi không rỗng")

        prompt = """
        Bạn là một AI y tế hỗ trợ bác sĩ. Dựa trên triệu chứng, suy luận các khả năng bệnh lý có thể xảy ra theo các bước:
        1. Phân tích triệu chứng.
        2. Liệt kê ít nhất 3 khả năng bệnh lý, xếp hạng theo khả năng.
        3. Giải thích lý do cho từng khả năng.
        Sử dụng ngôn ngữ y khoa chuyên nghiệp.

        Ví dụ:
        Triệu chứng: Ho kéo dài, khó thở, đau ngực.
        Trả lời:
        1. Viêm phổi (Khả năng cao): Triệu chứng ho và khó thở phù hợp với nhiễm trùng phổi.
        2. COPD (Khả năng trung bình): Ho kéo dài và khó thở có thể liên quan đến bệnh phổi tắc nghẽn mạn tính.
        3. Ung thư phổi (Khả năng thấp): Đau ngực và ho kéo dài có thể là dấu hiệu, nhưng cần thêm xét nghiệm.

        Triệu chứng: {symptoms}
        Trả lời:
        """
        prompt = prompt.format(symptoms=symptoms)
        contents = [{"role": "user", "parts": [{"text": prompt}]}]
        return self.gemini.generate_content(contents)