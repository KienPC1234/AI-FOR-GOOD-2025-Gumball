from .gemini_client import GeminiAI
from typing import List, Tuple


class DoctorEnhanceAI:
    def __init__(self):
        self.gemini = GeminiAI()

    def enhance_medical_record(self, medical_record: str) -> str:
        """
        Cải thiện bệnh án để rõ ràng và chuyên nghiệp hơn.

        Args:
            medical_record (str): Bệnh án cần cải thiện.

        Returns:
            str: Bệnh án đã được cải thiện.

        Raises:
            ValueError: Nếu bệnh án không hợp lệ.
        """
        if not isinstance(medical_record, str) or not medical_record.strip():
            raise ValueError("Bệnh án phải là chuỗi không rỗng")

        prompt = """
        Bạn là một AI y tế chuyên cải thiện bệnh án. Thực hiện các bước sau:
        1. Kiểm tra bệnh án để tìm lỗi về thông tin, định dạng hoặc thiếu sót.
        2. Cải thiện cách trình bày, đảm bảo rõ ràng và chuyên nghiệp.
        3. Bổ sung chi tiết nếu cần (ví dụ: xét nghiệm đề xuất, ghi chú theo dõi).
        4. Trả về bệnh án đã cải thiện.
        Bệnh án: {medical_record}
        Trả về:
        """
        prompt = prompt.format(medical_record=medical_record)
        contents = [{"role": "user", "parts": [{"text": prompt}]}]
        return self.gemini.generate_content(contents)

    def validate_diagnosis(
        self,
        symptoms: str,
        pathologies_list: List[List[Tuple[str, float]]],
        medical_record: str
    ) -> str:
        """
        Kiểm tra và xác nhận tính chính xác của chẩn đoán trong bệnh án.

        Args:
            symptoms (str): Triệu chứng của bệnh nhân.
            pathologies_list (List[List[Tuple[str, float]]]): Danh sách bệnh lý từ ảnh X-quang.
            medical_record (str): Bệnh án chứa chẩn đoán cần kiểm tra.

        Returns:
            str: Kết quả đánh giá và đề xuất cải tiến.

        Raises:
            ValueError: Nếu đầu vào không hợp lệ.
        """
        if not isinstance(symptoms, str) or not symptoms.strip():
            raise ValueError("Triệu chứng phải là chuỗi không rỗng")
        if not pathologies_list:
            raise ValueError("Danh sách bệnh lý không được rỗng")
        if not isinstance(medical_record, str) or not medical_record.strip():
            raise ValueError("Bệnh án phải là chuỗi không rỗng")

        prompt = """
        Bạn là một AI y tế chuyên kiểm tra và cải thiện chẩn đoán. Thực hiện các bước sau:
        1. So sánh chẩn đoán trong bệnh án với triệu chứng và kết quả X-quang.
        2. Xác định bất kỳ lỗi hoặc thiếu sót nào trong chẩn đoán.
        3. Đề xuất cải tiến hoặc xác nhận tính chính xác.
        4. Trả về kết quả đánh giá và đề xuất.
        Triệu chứng: {symptoms}
        Kết quả phân tích ảnh X-quang:
        """
        for i, pathologies in enumerate(pathologies_list):
            prompt += f"\nẢnh {i+1}:\n"
            for pathology, prob in pathologies:
                prompt += f"- {pathology}: Xác suất {prob:.2f}\n"
        prompt += f"\nBệnh án: {medical_record}\nTrả về:"
        
        prompt = prompt.format(symptoms=symptoms, medical_record=medical_record)
        contents = [{"role": "user", "parts": [{"text": prompt}]}]
        return self.gemini.generate_content(contents)