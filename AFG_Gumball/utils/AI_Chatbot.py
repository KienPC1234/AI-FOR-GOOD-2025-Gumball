import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
import io
from PIL import Image
from ..xray.xray import process_xray_image

class GeminiAI:
    def __init__(self, model="gemini-2.0-flash"):
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Không tìm thấy GEMINI_API_KEY trong biến môi trường")
        self.client = genai.Client(api_key=api_key)
        self.model = model

    def generate_content(self, contents):
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=contents
            )
            return response.text
        except Exception as e:
            raise RuntimeError(f"Lỗi khi tạo nội dung: {str(e)}")

class PatientAI:
    def __init__(self):
        self.gemini = GeminiAI()
        self.max_images = 5 

    def answer_question(self, question):
        # Kiểm tra đầu vào
        if not isinstance(question, str) or not question.strip():
            raise ValueError("Câu hỏi phải là chuỗi không rỗng")
        
        # Sử dụng Few-shot prompting
        prompt = """
        Bạn là một AI y tế thân thiện, hỗ trợ bệnh nhân với ngôn ngữ dễ hiểu, không dùng thuật ngữ y khoa phức tạp. Hãy trả lời ngắn gọn, rõ ràng và trấn an bệnh nhân.
        
        Ví dụ:
        Câu hỏi: "Tôi bị đau đầu thường xuyên, có sao không?"
        Trả lời: "Đau đầu có thể do nhiều nguyên nhân như căng thẳng hoặc thiếu nước. Bạn nên uống đủ nước, nghỉ ngơi và theo dõi thêm. Nếu đau đầu kéo dài, hãy đi khám bác sĩ."

        Câu hỏi từ bệnh nhân: {question}
        Trả lời:
        """
        contents = [prompt.format(question=question)]
        return self.gemini.generate_content(contents)

    def diagnose_images(self, image_bytes_list, symptoms=None, include_symptoms=False, include_xray_image=False):
        # Kiểm tra đầu vào
        if not image_bytes_list or len(image_bytes_list) > self.max_images:
            raise ValueError(f"Số lượng ảnh phải từ 1 đến {self.max_images}")
        if include_symptoms and (not isinstance(symptoms, str) or not symptoms.strip()):
            raise ValueError("Triệu chứng phải là chuỗi không rỗng khi được bao gồm")

        # Xử lý danh sách ảnh byte array (JPG)
        pathologies_list = []
        gradcam_images_list = []
        for img_bytes in image_bytes_list:
            try:
                # Kiểm tra định dạng ảnh
                img = Image.open(io.BytesIO(img_bytes))
                if img.format != "JPEG":
                    raise ValueError("Ảnh phải ở định dạng JPEG")
                
                # Chuyển byte array thành file tạm thời
                temp_path = "temp_xray.jpg"
                img.save(temp_path, format="JPEG")
                
                # Gọi hàm process_xray_image
                pathologies, gradcam_images = process_xray_image(temp_path)
                pathologies_list.append(pathologies)
                gradcam_images_list.append(gradcam_images)
            except Exception as e:
                raise RuntimeError(f"Lỗi khi xử lý ảnh: {str(e)}")
        
        # Tạo prompt với Chain-of-Thought
        prompt = """
        Bạn là một AI y tế hỗ trợ bệnh nhân. Dựa trên kết quả phân tích ảnh X-quang và ảnh X-quang gốc (nếu có), thực hiện các bước sau:
        1. Xem xét danh sách các bệnh lý được phát hiện với xác suất lớn hơn 0.5.
        2. Nếu có triệu chứng, kết hợp chúng để đưa ra chuẩn đoán chính xác hơn.
        3. Nếu có ảnh X-quang gốc, phân tích trực tiếp để bổ sung thông tin.
        4. Cung cấp chuẩn đoán dễ hiểu, giải thích ngắn gọn và hướng dẫn bệnh nhân nên làm gì tiếp theo.
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

        # Tạo danh sách nội dung
        contents = []
        if include_xray_image:
            for i, img_bytes in enumerate(image_bytes_list):
                contents.append(types.Part.from_bytes(
                    data=img_bytes,
                    mime_type='image/jpeg'
                ))
                contents.append(f"Phân tích ảnh X-quang {i+1} cùng với kết quả trên.")
        contents.append(prompt)

        # Gọi API
        diagnosis = self.gemini.generate_content(contents)
        
        # Trả về heatmap trực tiếp dưới dạng numpy array
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

class DoctorDiagnosticAI:
    def __init__(self):
        self.gemini = GeminiAI()
        self.max_images = 5

    def process_xray_image(self, img_path):
        # Kiểm tra đường dẫn ảnh
        if not os.path.exists(img_path):
            raise ValueError(f"Đường dẫn ảnh {img_path} không tồn tại")
        return process_xray_image(img_path)

    def create_medical_record(self, patient_info, symptoms, image_paths, include_xray_image=False):
        # Kiểm tra đầu vào
        if not isinstance(patient_info, str) or not patient_info.strip():
            raise ValueError("Thông tin bệnh nhân phải là chuỗi không rỗng")
        if not isinstance(symptoms, str) or not symptoms.strip():
            raise ValueError("Triệu chứng phải là chuỗi không rỗng")
        if not image_paths or len(image_paths) > self.max_images:
            raise ValueError(f"Số lượng ảnh phải từ 1 đến {self.max_images}")

        # Xử lý ảnh X-quang
        pathologies_list = []
        gradcam_images_list = []
        image_bytes_list = []
        for img_path in image_paths:
            pathologies, gradcam_images = self.process_xray_image(img_path)
            pathologies_list.append(pathologies)
            gradcam_images_list.append(gradcam_images)
            if include_xray_image:
                with open(img_path, 'rb') as f:
                    image_bytes_list.append(f.read())
        
        # Tạo prompt với Few-shot prompting
        prompt = """
        Bạn là một AI y tế chuyên nghiệp hỗ trợ bác sĩ. Dựa trên thông tin bệnh nhân, triệu chứng, kết quả phân tích ảnh X-quang và ảnh X-quang gốc (nếu có), tạo một bệnh án chi tiết theo các bước:
        1. Ghi nhận thông tin bệnh nhân.
        2. Liệt kê triệu chứng.
        3. Phân tích kết quả ảnh X-quang.
        4. Nếu có ảnh X-quang gốc, phân tích trực tiếp để bổ sung thông tin.
        5. Đưa ra chuẩn đoán sơ bộ.
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
        - Chuẩn đoán sơ bộ: Viêm phổi cấp.
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

        # Tạo danh sách nội dung
        contents = []
        if include_xray_image:
            for i, img_bytes in enumerate(image_bytes_list):
                contents.append(types.Part.from_bytes(
                    data=img_bytes,
                    mime_type='image/jpeg'
                ))
                contents.append(f"Phân tích ảnh X-quang {i+1} cùng với kết quả trên.")
        contents.append(prompt)

        # Gọi API
        return self.gemini.generate_content(contents)

    def suggest_treatment(self, symptoms, pathologies_list):
        # Kiểm tra đầu vào
        if not isinstance(symptoms, str) or not symptoms.strip():
            raise ValueError("Triệu chứng phải là chuỗi không rỗng")
        if not pathologies_list:
            raise ValueError("Danh sách bệnh lý không được rỗng")

        # Chain-of-Thought prompting
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
        contents = [prompt]
        return self.gemini.generate_content(contents)

    def reason_from_symptoms(self, symptoms):
        # Kiểm tra đầu vào
        if not isinstance(symptoms, str) or not symptoms.strip():
            raise ValueError("Triệu chứng phải là chuỗi không rỗng")

        # Few-shot prompting
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
        contents = [prompt]
        return self.gemini.generate_content(contents)

class DoctorEnhanceAI:
    def __init__(self):
        self.gemini = GeminiAI()

    def improve_medical_record(self, medical_record):
        # Kiểm tra đầu vào
        if not isinstance(medical_record, str) or not medical_record.strip():
            raise ValueError("Bệnh án phải là chuỗi không rỗng")

        # Chain-of-Thought prompting
        prompt = """
        Bạn là một AI y tế chuyên cải thiện bệnh án. Thực hiện các bước sau:
        1. Kiểm tra bệnh án để tìm lỗi về thông tin, định dạng hoặc thiếu sót.
        2. Cải thiện cách trình bày, đảm bảo rõ ràng và chuyên nghiệp.
        3. Bổ sung chi tiết nếu cần (ví dụ: xét nghiệm đề xuất, ghi chú theo dõi).
        4. Trả về bệnh án đã cải thiện.
        Bệnh án: {medical_record}
        """
        prompt = prompt.format(medical_record=medical_record)
        contents = [prompt]
        return self.gemini.generate_content(contents)

    def validate_diagnosis(self, diagnosis, symptoms, pathologies_list):
        # Kiểm tra đầu vào
        if not isinstance(diagnosis, str) or not diagnosis.strip():
            raise ValueError("Chuẩn đoán phải là chuỗi không rỗng")
        if not isinstance(symptoms, str) or not symptoms.strip():
            raise ValueError("Triệu chứng phải là chuỗi không rỗng")
        if not pathologies_list:
            raise ValueError("Danh sách bệnh lý không được rỗng")

        # Chain-of-Thought prompting
        prompt = """
        Bạn là một AI y tế chuyên kiểm tra và cải thiện chuẩn đoán. Thực hiện các bước sau:
        1. So sánh chuẩn đoán với triệu chứng và kết quả X-quang.
        2. Xác định bất kỳ lỗi hoặc thiếu sót nào trong chuẩn đoán.
        3. Đề xuất cải tiến hoặc xác nhận tính chính xác.
        4. Trả về kết quả đánh giá và đề xuất.
        Chuẩn đoán: {diagnosis}
        Triệu chứng: {symptoms}
        Kết quả phân tích ảnh X-quang:
        """
        for i, pathologies in enumerate(pathologies_list):
            prompt += f"\nẢnh {i+1}:\n"
            for pathology, prob in pathologies:
                prompt += f"- {pathology}: Xác suất {prob:.2f}\n"
        
        prompt = prompt.format(diagnosis=diagnosis, symptoms=symptoms)
        contents = [prompt]
        return self.gemini.generate_content(contents)