import torch
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import io
from scipy.ndimage import zoom
from AFG_Gumball.xray.xray import BodyPart, get_body_part_segment, load_xray_image  # Import từ module

# Hàm hiển thị ảnh gốc và vùng phân đoạn
def display_segmented_image(original_image, segment, part_name):
    """
    Hiển thị ảnh X-ray gốc và vùng phân đoạn của một bộ phận.
    
    Args:
        original_image: Ảnh X-ray gốc (numpy array).
        segment: Vùng phân đoạn (numpy array, shape [512, 512]).
        part_name: Tên bộ phận (str).
    """
    plt.figure(figsize=(10, 5))
    
    # Hiển thị ảnh gốc
    plt.subplot(1, 2, 1)
    plt.imshow(original_image, cmap='gray')
    plt.title('Ảnh X-ray gốc')
    plt.axis('off')
    
    # Hiển thị vùng phân đoạn
    plt.subplot(1, 2, 2)
    plt.imshow(original_image, cmap='gray')
    plt.imshow(segment, cmap='jet', alpha=0.5)  # Overlay vùng phân đoạn
    plt.title(f'Vùng phân đoạn: {part_name}')
    plt.axis('off')
    
    plt.tight_layout()
    plt.show()



# Ví dụ sử dụng
if __name__ == "__main__":
    # Tải ảnh xray.png từ đường dẫn
    image_path = "xray.jpg"
    image_tensor = load_xray_image(image_path)
    
    # Tải ảnh gốc để hiển thị (vì load_xray_image chỉ trả về tensor)
    original_image = Image.open(image_path).convert("L")
    original_image_np = np.array(original_image.resize((512, 512), Image.Resampling.LANCZOS))
    
    # Lấy vùng phân đoạn của tim (HEART)
    heart_segment = get_body_part_segment(image_tensor, BodyPart.HEART)
    
    # Chuyển tensor segment sang numpy
    heart_segment_np = heart_segment.detach().numpy()  # Shape: [512, 512]
    
    # Hiển thị ảnh gốc và vùng phân đoạn
    display_segmented_image(original_image_np, heart_segment_np, "Heart")
    
    # Ví dụ sử dụng với image byte
    with open("xray.jpg", "rb") as f:
        image_bytes = f.read()
    image_tensor_from_bytes = load_xray_image(image_bytes)
    # Có thể tái sử dụng image_tensor_from_bytes tương tự