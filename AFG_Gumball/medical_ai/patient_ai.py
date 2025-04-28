from .gemini_client import GeminiAI
from PIL import Image
import io
import os
import tempfile
from ..xray_processing import process_xray_image
import google.generativeai as genai


class PatientAI:
    def __init__(self):
        self.gemini = GeminiAI()
        self.max_images = 5

    def answer_question(self, question: str) -> str:
        """
        Trả lời câu hỏi của bệnh nhân bằng ngôn ngữ thân thiện, dễ hiểu.

        Args:
            question (str): Câu hỏi từ bệnh nhân.

        Returns:
            str: Câu trả lời thân thiện.

        Raises:
            ValueError: Nếu câu hỏi không hợp lệ.
        """
        if not isinstance(question, str) or not question.strip():
            raise ValueError("Câu hỏi phải là chuỗi không rỗng")
        
        prompt = """
        Bạn là một AI y tế thân thiện, hỗ trợ bệnh nhân với ngôn ngữ dễ hiểu, không dùng thuật ngữ y khoa phức tạp. Hãy trả lời ngắn gọn, rõ ràng và trấn an bệnh nhân.
        
        Ví dụ:
        Câu hỏi: "Tôi bị đau đầu thường xuyên, có sao không?"
        Trả lời: "Đau đầu có thể do nhiều nguyên nhân như căng thẳng hoặc thiếu nước. Bạn nên uống đủ nước, nghỉ ngơi và theo dõi thêm. Nếu đau đầu kéo dài, hãy đi khám bác sĩ."

        Câu hỏi từ bệnh nhân: {question}
        Trả lời:
        """
        contents = [{"role": "user", "parts": [{"text": prompt.format(question=question)}]}]
        return self.gemini.generate_content(contents)

    def diagnose_images(
        self,
        image_bytes_list: list[bytes],
        symptoms: str | None = None,
        include_symptoms: bool = False,
        include_xray_image: bool = False
    ) -> tuple[str, list[dict]]:
        """
        Chẩn đoán dựa trên ảnh X-quang và triệu chứng (nếu có).

        Args:
            image_bytes_list (list[bytes]): Danh sách dữ liệu bytes của ảnh X-quang.
            symptoms (str, optional): Triệu chứng của bệnh nhân.
            include_symptoms (bool): Bao gồm triệu chứng trong chẩn đoán.
            include_xray_image (bool): Bao gồm ảnh X-quang gốc trong phân tích.

        Returns:
            tuple[str, list[dict]]: Chẩn đoán (chuỗi) và danh sách heatmap (mỗi heatmap chứa pathology, probability, heatmap_array).

        Raises:
            ValueError: Nếu đầu vào không hợp lệ.
            RuntimeError: Nếu xử lý ảnh thất bại.
        """
        if not image_bytes_list or len(image_bytes_list) > self.max_images:
            raise ValueError(f"Số lượng ảnh phải từ 1 đến {self.max_images}")
        if include_symptoms and (not isinstance(symptoms, str) or not symptoms.strip()):
            raise ValueError("Triệu chứng phải là chuỗi không rỗng khi được bao gồm")

        pathologies_list = []
        gradcam_images_list = []
        temp_files = []
        for img_bytes in image_bytes_list:
            try:
                img = Image.open(io.BytesIO(img_bytes))
                if img.format != "JPEG":
                    raise ValueError("Ảnh phải ở định dạng JPEG")
                
                # Lưu ảnh tạm để sử dụng với process_xray_image và upload
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                    img.save(tmp.name, format="JPEG")
                    temp_files.append(tmp.name)
                
                pathologies, gradcam_images = process_xray_image(temp_files[-1])
                pathologies_list.append(pathologies)
                gradcam_images_list.append(gradcam_images)
            except Exception as e:
                raise RuntimeError(f"Lỗi khi xử lý ảnh: {str(e)}")
        
        prompt = """
        Bạn là một AI y tế hỗ trợ bệnh nhân. Dựa trên kết quả phân tích ảnh X-quang và ảnh X-quang gốc (nếu có), thực hiện các bước sau:
        1. Xem xét danh sách các bệnh lý được phát hiện với xác suất lớn hơn 0.5.
        2. Nếu có triệu chứng, kết hợp chúng để đưa ra chẩn đoán chính xác hơn.
        3. Nếu có ảnh X-quang gốc, phân tích trực tiếp để bổ sung thông tin.
        4. Cung cấp chẩn đoán dễ hiểu, giải thích ngắn gọn và hướng dẫn bệnh nhân nên làm gì tiếp theo.
        5. Đảm bảo ngôn ngữ đơn giản, trấn an và khuyên bệnh nhân gặp bác sĩ nếu cần.

        Kết quả phân tích ảnh X-quang:
        """
        for i, (pathologies, gradcam) in enumerate(zip(pathologies_list, gradcam_images_list)):
            prompt += f"\nẢnh {i+1}:\n"
            for pathology, prob in pathologies:
                prompt += f"- {pathology}: Xác suất {prob:.2f}\n"
        
        if include_symptoms and symptoms:
            prompt += f"\nTriệu chứng từ bệnh nhân: {symptoms}\n"
        
        prompt += "\nTrả lời:"

        contents = []
        if include_xray_image:
            for i, temp_file in enumerate(temp_files):
                try:
                    file_uri = self.gemini.upload_file(temp_file)
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

        try:
            diagnosis = self.gemini.generate_content(contents)
        finally:
            # Xóa file tạm
            for temp_file in temp_files:
                try:
                    os.remove(temp_file)
                except OSError as e:
                    print(f"Cảnh báo: Không thể xóa file tạm {temp_file}: {str(e)}")
        
        heatmap_arrays = []
        for i, gradcam_images in enumerate(gradcam_images_list):
            for gradcam in gradcam_images:
                heatmap = gradcam["heatmap"]
                heatmap_arrays.append({
                    "pathology": gradcam["pathology"],
                    "probability": gradcam["probability"],
                    "heatmap_array": heatmap
                })
        
        return diagnosis, heatmap_arrays