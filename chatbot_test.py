import os
import io
from PIL import Image
from AFG_Gumball.medical_ai import PatientAI, DoctorDiagnosticAI, DoctorEnhanceAI, XrayAnalysisExpertAI
import tempfile

def test_system(image_path: str = "xray.jpg") -> None:
    """
    Kiểm tra toàn bộ hệ thống chẩn đoán y tế của module AFG_Gumball.

    Args:
        image_path (str): Đường dẫn đến ảnh X-quang mẫu (mặc định: 'xray.jpg').

    Raises:
        FileNotFoundError: Nếu ảnh X-quang hoặc file .env không tồn tại.
        RuntimeError: Nếu có lỗi trong quá trình xử lý AI.
    """
    print("=== Bắt đầu kiểm tra hệ thống chẩn đoán y tế ===")

    # Kiểm tra file ảnh tồn tại
    if not os.path.exists(image_path):
        print(f"Cảnh báo: Ảnh {image_path} không tồn tại, sử dụng ảnh giả lập.")
        img = Image.new("L", (512, 512), color=128)  # Ảnh xám giả lập
        # Lưu ảnh giả lập vào file tạm
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            img.save(tmp.name, format="JPEG")
            image_path = tmp.name
    else:
        img = Image.open(image_path).convert("L")

    # Chuẩn bị dữ liệu ảnh bytes và paths
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="JPEG")
    image_bytes_list = [img_byte_arr.getvalue()]
    symptoms = "Ho kéo dài, đau ngực, khó thở"
    image_paths = [image_path]

    # Khởi tạo pathologies_list mặc định
    pathologies_list = []

    # 1. Kiểm tra PatientAI
    print("\n1. Kiểm tra PatientAI...")
    try:
        patient_ai = PatientAI()
        print("PatientAI khởi tạo thành công")

        # 1.1. Test trả lời câu hỏi bệnh nhân
        question = "Tôi bị ho và đau ngực, có sao không?"
        response = patient_ai.answer_question(question)
        print(f"Câu hỏi: {question}")
        print(f"Trả lời: {response}")

        # 1.2. Test chẩn đoán ảnh X-quang
        print("\n1.2.1. Chẩn đoán chỉ với kết quả X-quang:")
        diagnosis, heatmap_arrays = patient_ai.diagnose_images(
            image_bytes_list, symptoms, include_symptoms=True, include_xray_image=False
        )
        print(f"Chẩn đoán: {diagnosis}")
        print("Heatmap arrays:")
        for h in heatmap_arrays:
            print(f"- Bệnh lý: {h['pathology']}, Xác suất: {h['probability']:.2f}, Shape: {h['heatmap_array'].shape}")

        print("\n1.2.2. Chẩn đoán kết hợp với ảnh X-quang gốc:")
        diagnosis_with_image, heatmap_arrays_with_image = patient_ai.diagnose_images(
            image_bytes_list, symptoms, include_symptoms=True, include_xray_image=True
        )
        print(f"Chẩn đoán: {diagnosis_with_image}")
        print("Heatmap arrays:")
        for h in heatmap_arrays_with_image:
            print(f"- Bệnh lý: {h['pathology']}, Xác suất: {h['probability']:.2f}, Shape: {h['heatmap_array'].shape}")
    except Exception as e:
        print(f"Lỗi khi kiểm tra PatientAI: {str(e)}")

    # 2. Kiểm tra DoctorDiagnosticAI
    print("\n2. Kiểm tra DoctorDiagnosticAI...")
    try:
        doctor_diag_ai = DoctorDiagnosticAI()
        print("DoctorDiagnosticAI khởi tạo thành công")

        # 2.1. Test tạo bệnh án
        patient_info = "Nữ, 50 tuổi, tiền sử cao huyết áp"
        medical_record = doctor_diag_ai.create_medical_record(
            patient_info, symptoms, image_paths, include_xray_image=False
        )
        print(f"Bệnh án (không dùng ảnh gốc): {medical_record}")

        # 2.2. Test tạo bệnh án với ảnh X-quang gốc
        medical_record_with_image = doctor_diag_ai.create_medical_record(
            patient_info, symptoms, image_paths, include_xray_image=True
        )
        print(f"Bệnh án (kết hợp ảnh gốc): {medical_record_with_image}")

        # 2.3. Test gợi ý điều trị
        pathologies_list = [doctor_diag_ai.process_xray_image(img_path)[0] for img_path in image_paths]
        treatment = doctor_diag_ai.suggest_treatment(symptoms, pathologies_list)
        print(f"Gợi ý điều trị: {treatment}")

        # 2.4. Test suy luận từ triệu chứng
        reasoning = doctor_diag_ai.reason_from_symptoms(symptoms)
        print(f"Suy luận từ triệu chứng: {reasoning}")
    except Exception as e:
        print(f"Lỗi khi kiểm tra DoctorDiagnosticAI: {str(e)}")

    # 3. Kiểm tra DoctorEnhanceAI
    print("\n3. Kiểm tra DoctorEnhanceAI...")
    try:
        doctor_enhance_ai = DoctorEnhanceAI()
        print("DoctorEnhanceAI khởi tạo thành công")

        # 3.1. Test cải thiện bệnh án
        improved_record = doctor_enhance_ai.enhance_medical_record(medical_record)
        print(f"Bệnh án cải thiện: {improved_record}")

        # 3.2. Test kiểm tra chẩn đoán
        if pathologies_list:  # Chỉ kiểm tra nếu pathologies_list không rỗng
            validation = doctor_enhance_ai.validate_diagnosis(symptoms, pathologies_list,medical_record)
            print(f"Kiểm tra chẩn đoán: {validation}")
        else:
            print("Bỏ qua kiểm tra chẩn đoán: Không có dữ liệu bệnh lý")
    except Exception as e:
        print(f"Lỗi khi kiểm tra DoctorEnhanceAI: {str(e)}")

    # 4. Kiểm tra XrayAnalysisExpertAI
    print("\n4. Kiểm tra XrayAnalysisExpertAI...")
    try:
        expert_ai = XrayAnalysisExpertAI()
        print("XrayAnalysisExpertAI khởi tạo thành công")
        result = expert_ai.analyze_xray(image_paths, symptoms)
        print(f"Kết quả phân tích X-quang: {result}")
    except Exception as e:
        print(f"Lỗi khi kiểm tra XrayAnalysisExpertAI: {str(e)}")
    finally:
        # Xóa file tạm nếu dùng ảnh giả lập
        if not os.path.exists("xray.jpg") and os.path.exists(image_path):
            try:
                os.remove(image_path)
            except OSError as e:
                print(f"Cảnh báo: Không thể xóa file tạm {image_path}: {str(e)}")

    print("\n=== Kiểm tra hoàn tất ===")


if __name__ == "__main__":
    # Hướng dẫn thêm API key
    print("=== Hướng dẫn thêm API key ===")
    print("1. Tạo file .env trong thư mục dự án với nội dung:")
    print("   GEMINI_API_KEY=your_actual_api_key_here")
    print("2. Thay 'your_actual_api_key_here' bằng API key thực tế từ Google.")
    print("3. Đảm bảo file .env không được commit lên git (thêm vào .gitignore).")
    print("4. Nếu không dùng .env, có thể set biến môi trường trực tiếp:")
    print("   Windows: set GEMINI_API_KEY=your_actual_api_key_here")
    print("   Linux/Mac: export GEMINI_API_KEY=your_actual_api_key_here")
    print("================================\n")

    # Chạy kiểm tra
    try:
        test_system()
    except Exception as e:
        print(f"Lỗi hệ thống: {str(e)}")