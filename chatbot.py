import os
import io
from PIL import Image
from AFG_Gumball.utils.AI_Chatbot import PatientAI, DoctorDiagnosticAI, DoctorEnhanceAI

def test_system():
    print("=== Bắt đầu kiểm tra hệ thống chẩn đoán y tế ===")
    
    try:
        # 1. Kiểm tra khởi tạo PatientAI
        print("\n1. Kiểm tra PatientAI...")
        patient_ai = PatientAI()
        print("PatientAI khởi tạo thành công")

        # 1.1. Test trả lời câu hỏi bệnh nhân
        question = "Tôi bị ho và đau ngực, có sao không?"
        response = patient_ai.answer_question(question)
        print(f"Câu hỏi: {question}")
        print(f"Trả lời: {response}")

        # 1.2. Test chẩn đoán ảnh X-quang
        # Tạo dữ liệu ảnh mẫu (giả lập)
        img = Image.new('L', (512, 512), color=128)  # Ảnh xám giả lập
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format="JPEG")
        image_bytes_list = [img_byte_arr.getvalue()]
        symptoms = "Ho kéo dài, đau ngực, khó thở"
        
        # Test chẩn đoán chỉ với kết quả X-quang
        print("\n1.2.1. Chẩn đoán chỉ với kết quả X-quang:")
        diagnosis, heatmap_arrays = patient_ai.diagnose_images(
            image_bytes_list, symptoms, include_symptoms=True, include_xray_image=False
        )
        print(f"Chẩn đoán: {diagnosis}")
        print("Heatmap arrays:")
        for h in heatmap_arrays:
            print(f"- Bệnh lý: {h['pathology']}, Xác suất: {h['probability']:.2f}, Shape: {h['heatmap_array'].shape}")

        # Test chẩn đoán kết hợp với ảnh X-quang gốc
        print("\n1.2.2. Chẩn đoán kết hợp với ảnh X-quang gốc:")
        diagnosis_with_image, heatmap_arrays_with_image = patient_ai.diagnose_images(
            image_bytes_list, symptoms, include_symptoms=True, include_xray_image=True
        )
        print(f"Chẩn đoán: {diagnosis_with_image}")
        print("Heatmap arrays:")
        for h in heatmap_arrays_with_image:
            print(f"- Bệnh lý: {h['pathology']}, Xác suất: {h['probability']:.2f}, Shape: {h['heatmap_array'].shape}")

        # 2. Kiểm tra DoctorDiagnosticAI
        print("\n2. Kiểm tra DoctorDiagnosticAI...")
        doctor_diag_ai = DoctorDiagnosticAI()
        print("DoctorDiagnosticAI khởi tạo thành công")

        # 2.1. Test tạo bệnh án (không dùng ảnh gốc)
        patient_info = "Nữ, 50 tuổi, tiền sử cao huyết áp"
        image_paths = ["xray.jpg"]  # Thay bằng đường dẫn thực tế
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

        # 3. Kiểm tra DoctorEnhanceAI
        print("\n3. Kiểm tra DoctorEnhanceAI...")
        doctor_enhance_ai = DoctorEnhanceAI()
        print("DoctorEnhanceAI khởi tạo thành công")

        # 3.1. Test cải thiện bệnh án
        improved_record = doctor_enhance_ai.improve_medical_record(medical_record)
        print(f"Bệnh án cải thiện: {improved_record}")

        # 3.2. Test kiểm tra chẩn đoán
        validation = doctor_enhance_ai.validate_diagnosis(medical_record, symptoms, pathologies_list)
        print(f"Kiểm tra chẩn đoán: {validation}")

        print("\n=== Kiểm tra hoàn tất ===")

    except Exception as e:
        print(f"Lỗi trong quá trình kiểm tra: {str(e)}")

if __name__ == "__main__":
    # Hướng dẫn thêm API key
    print("=== Hướng dẫn thêm API key ===")
    print("1. Tạo file .env trong thư mục dự án với nội dung:")
    print("   GEMINI_API_KEY=your_actual_api_key_here")
    print("2. Thay 'your_actual_api_key_here' bằng API key thực tế từ Google.")
    print("3. Đảm bảo file .env không được commit lên git (thêm vào .gitignore).")
    print("4. Nếu không dùng .env, có thể set biến môi trường trực tiếp:")
    print("   set GEMINI_API_KEY=your_actual_api_key_here (Windows)")
    print("================================\n")

    # Chạy kiểm tra
    test_system()