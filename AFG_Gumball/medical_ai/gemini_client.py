import os
import google.generativeai as genai
from typing import List, Any, Dict
from dotenv import load_dotenv

class GeminiAI:
    def __init__(self, model: str = "gemini-2.0-flash"):
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY không được thiết lập trong biến môi trường hoặc file .env")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)
    
    def upload_file(self, file_path: str) -> str:
        """
        Tải file lên Google AI và trả về URI của file.

        Args:
            file_path (str): Đường dẫn đến file cần tải lên.

        Returns:
            str: URI của file đã tải lên.

        Raises:
            ValueError: Nếu file không tồn tại hoặc không hợp lệ.
            RuntimeError: Nếu tải file thất bại.
        """
        if not os.path.exists(file_path):
            raise ValueError(f"File {file_path} không tồn tại")
        
        try:
            response = genai.upload_file(file_path, mime_type="image/jpeg")
            return response.uri
        except Exception as e:
            raise RuntimeError(f"Lỗi khi tải file lên: {str(e)}")
    
    def generate_content(self, contents: List[Dict[str, Any]]) -> str:
        """
        Tạo nội dung sử dụng Gemini AI.

        Args:
            contents (List[Dict[str, Any]]): Nội dung đầu vào, mỗi phần tử là một dictionary chứa 'role' và 'parts'.

        Returns:
            str: Nội dung được tạo ra.

        Raises:
            RuntimeError: Nếu tạo nội dung thất bại.
            ValueError: Nếu định dạng contents không hợp lệ.
        """
        for item in contents:
            if "role" not in item or item["role"] not in ["user", "model"]:
                raise ValueError("Mỗi phần tử trong contents phải có trường 'role' với giá trị 'user' hoặc 'model'")
            if "parts" not in item or not item["parts"]:
                raise ValueError("Mỗi phần tử trong contents phải có trường 'parts' không rỗng")
        
        try:
            response = self.model.generate_content(contents)
            return response.text
        except Exception as e:
            raise RuntimeError(f"Lỗi khi tạo nội dung: {str(e)}")