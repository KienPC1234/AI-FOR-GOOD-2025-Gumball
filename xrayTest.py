import torch
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import io
from AFG_Gumball.xray_processing import load_xray_image, get_body_part_segment, BodyPart


def display_segmented_image(original_image: np.ndarray, segment: np.ndarray, part_name: str) -> None:
    """
    Hiển thị ảnh X-quang gốc và vùng phân đoạn của một bộ phận cơ thể.

    Args:
        original_image (np.ndarray): Ảnh X-quang gốc dưới dạng mảng numpy, kích thước [512, 512].
        segment (np.ndarray): Vùng phân đoạn, kích thước [512, 512].
        part_name (str): Tên bộ phận cơ thể (ví dụ: 'Heart', 'Left Lung').

    Raises:
        ValueError: Nếu đầu vào không hợp lệ (ví dụ: kích thước sai).
    """
    if not isinstance(original_image, np.ndarray) or not isinstance(segment, np.ndarray):
        raise ValueError("original_image và segment phải là mảng numpy")
    if original_image.shape[:2] != (512, 512) or segment.shape != (512, 512):
        raise ValueError("Kích thước ảnh và vùng phân đoạn phải là [512, 512]")

    plt.figure(figsize=(10, 5))

    # Hiển thị ảnh gốc
    plt.subplot(1, 2, 1)
    plt.imshow(original_image, cmap="gray")
    plt.title("Ảnh X-quang gốc")
    plt.axis("off")

    # Hiển thị ảnh gốc với vùng phân đoạn overlay
    plt.subplot(1, 2, 2)
    plt.imshow(original_image, cmap="gray")
    plt.imshow(segment, cmap="jet", alpha=0.5)  # Overlay vùng phân đoạn
    plt.title(f"Vùng phân đoạn: {part_name}")
    plt.axis("off")

    plt.tight_layout()
    plt.show()


def process_and_display_xray(image_input: str | bytes, body_part: BodyPart = BodyPart.HEART) -> None:
    """
    Xử lý và hiển thị ảnh X-quang với vùng phân đoạn của một bộ phận cơ thể.

    Args:
        image_input (str or bytes): Đường dẫn file ảnh hoặc dữ liệu bytes của ảnh X-quang.
        body_part (BodyPart): Bộ phận cơ thể cần phân đoạn (mặc định là HEART).

    Raises:
        FileNotFoundError: Nếu đường dẫn file không tồn tại.
        ValueError: Nếu định dạng ảnh không hợp lệ hoặc xử lý thất bại.
    """
    # Tải ảnh X-quang
    try:
        image_tensor = load_xray_image(image_input)
    except Exception as e:
        raise ValueError(f"Lỗi khi tải ảnh X-quang: {str(e)}")

    # Tải ảnh gốc để hiển thị
    try:
        if isinstance(image_input, str):
            original_image = Image.open(image_input).convert("L")
        else:  # image_input là bytes
            original_image = Image.open(io.BytesIO(image_input)).convert("L")
    except FileNotFoundError:
        raise FileNotFoundError(f"Không tìm thấy file: {image_input}")
    except Exception as e:
        raise ValueError(f"Lỗi khi mở ảnh: {str(e)}")

    # Resize ảnh gốc về kích thước 512x512
    try:
        original_image_np = np.array(original_image.resize((512, 512), Image.Resampling.LANCZOS))
    except Exception as e:
        raise ValueError(f"Lỗi khi resize ảnh: {str(e)}")

    # Lấy vùng phân đoạn
    try:
        segment = get_body_part_segment(image_tensor, body_part)
        segment_np = segment.detach().cpu().numpy()  # Chuyển tensor sang numpy
    except Exception as e:
        raise ValueError(f"Lỗi khi phân đoạn bộ phận {body_part.name}: {str(e)}")

    # Hiển thị ảnh và vùng phân đoạn
    display_segmented_image(original_image_np, segment_np, body_part.name.replace("_", " ").title())


if __name__ == "__main__":
    # Ví dụ sử dụng với đường dẫn file
    try:
        image_path = "xray.jpg"
        process_and_display_xray(image_path, BodyPart.HEART)
    except Exception as e:
        print(f"Lỗi khi xử lý với file: {str(e)}")

    # Ví dụ sử dụng với image bytes
    try:
        with open("xray.jpg", "rb") as f:
            image_bytes = f.read()
        process_and_display_xray(image_bytes, BodyPart.LEFT_LUNG)
    except Exception as e:
        print(f"Lỗi khi xử lý với bytes: {str(e)}")