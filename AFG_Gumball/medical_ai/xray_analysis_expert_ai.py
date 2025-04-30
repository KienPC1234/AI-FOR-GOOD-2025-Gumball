from .gemini_client import GeminiAI
from PIL import Image
from numpy import ndarray
import io
import json
import os
from typing import Optional, Collection
import google.generativeai as genai


class XrayAnalysisExpertAI:
    def __init__(self):
        self.gemini = GeminiAI()
        self.max_images = 5

    def analyze_xray(self,
            symptoms: str,
            image_paths: Optional[Collection[str]] = None,
        ) -> dict:
        """
        Phân tích ảnh X-quang gốc và triệu chứng.
        Trả về chẩn đoán và danh sách khu vực có khả năng bệnh lý.

        Args:
            image_paths (list[str]): Danh sách đường dẫn đến các file ảnh X-quang.
            symptoms (str): Triệu chứng của bệnh nhân.

        Returns:
            dict: JSON chứa chẩn đoán, vùng bất thường, và lời khuyên.

        Raises:
            ValueError: Nếu đầu vào không hợp lệ.
            RuntimeError: Nếu xử lý thất bại.
        """
        
        if not image_paths or len(image_paths) > self.max_image:
            raise ValueError(f"Số lượng ảnh phải nằm trong khoảng từ 1 đến {self.max_images}")
        if not symptoms.strip():
            raise ValueError("Triệu chứng phải là chuỗi không rỗng")

        for img_path in image_paths:
            if not os.path.exists(img_path):
                raise ValueError(f"Đường dẫn ảnh {img_path} không tồn tại")
            try:
                img = Image.open(img_path)
                if img.format != "JPEG":
                    raise ValueError(f"Ảnh {img_path} phải ở định dạng JPEG")
            except Exception as e:
                raise RuntimeError(f"Lỗi khi xử lý ảnh {img_path}: {str(e)}")

        prompt = f"""
        Bạn là một chuyên gia phân tích ảnh X-quang, hỗ trợ bác sĩ và bệnh nhân. Dựa trên ảnh X-quang gốc và triệu chứng, thực hiện các bước sau:
        1. Phân tích ảnh X-quang để xác định các khu vực bất thường (mô tả vị trí, đặc điểm như mờ, đường kẻ, vùng sáng/tối, v.v.).
        2. Kết hợp triệu chứng để đưa ra chẩn đoán sơ bộ.
        3. Đánh dấu các khu vực có khả năng bệnh lý (mô tả vị trí và loại bệnh lý nghi ngờ).
        4. Cung cấp lời khuyên cho bệnh nhân, sử dụng ngôn ngữ dễ hiểu, trấn an.
        5. Trả về kết quả dạng JSON với các trường:
           - diagnosis: Chẩn đoán sơ bộ (chuỗi).
           - abnormal_areas: Danh sách các khu vực bất thường, mỗi khu vực có:
             - location: Vị trí (ví dụ: "phổi trái, vùng dưới", "phổi phải, vùng trên").
             - description: Mô tả đặc điểm bất thường (ví dụ: "vùng mờ", "đường Kerley B").
             - suspected_pathology: Bệnh lý nghi ngờ (ví dụ: "viêm phổi", "tràn dịch màng phổi").
           - advice: Lời khuyên cho bệnh nhân (chuỗi).

        Ví dụ:
        Triệu chứng: Ho kéo dài, khó thở.
        Ảnh X-quang: [Ảnh được gửi kèm].
        Trả về:
        {{
          "diagnosis": "Nghi ngờ viêm phổi hoặc tràn dịch màng phổi.",
          "abnormal_areas": [
            {{
              "location": "phổi phải, vùng dưới",
              "description": "vùng mờ lan tỏa",
              "suspected_pathology": "viêm phổi"
            }},
            {{
              "location": "phổi trái, vùng ngoại vi",
              "description": "đường Kerley B",
              "suspected_pathology": "tràn dịch màng phổi"
            }}
          ],
          "advice": "Bạn nên đi khám bác sĩ ngay để được xét nghiệm thêm. Nghỉ ngơi, uống nhiều nước và tránh khói bụi."
        }}

        Triệu chứng: {symptoms}
        Trả về (chỉ trả về JSON):
        """

        contents = []
        for i, img_path in enumerate(image_paths):
            try:
                file_uri = self.gemini.upload_file(img_path)
                contents.append({
                    "role": "user",
                    "parts": [
                        {"file_data": {"file_uri": file_uri, "mime_type": "image/jpeg"}},
                        {"text": f"Phân tích ảnh X-quang {i + 1}."}
                    ]
                })
            except Exception as e:
                raise RuntimeError(f"Lỗi khi tải ảnh lên: {str(e)}")
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        result = self.gemini.generate_content(contents)

        try:
            start = result.find('{')
            end = result.rfind('}') + 1
            if start == -1 or end == -1:
                raise RuntimeError("Không tìm thấy JSON trong kết quả trả về")

            clean_json_text = result[start:end]
            result_json = json.loads(clean_json_text)

            if not all(key in result_json for key in ["diagnosis", "abnormal_areas", "advice"]):
                raise RuntimeError("JSON trả về thiếu trường bắt buộc")

            return result_json
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Kết quả trả về từ Gemini API không phải JSON hợp lệ: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Lỗi khi xử lý kết quả trả về: {str(e)}")