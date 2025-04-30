import skimage.io
import numpy as np
import torch
import torchvision.transforms as transforms
from PIL import Image
import io
from ..torchxrayvision import datasets
from .model_utils import get_model

def load_xray_image(image_input):
    """
    Tải và tiền xử lý ảnh X-ray từ đường dẫn file hoặc image byte.
    
    Args:
        image_input: Đường dẫn file ảnh (str) hoặc dữ liệu ảnh dạng bytes.
    
    Returns:
        Tensor ảnh X-ray đã tiền xử lý, shape [1, 512, 512].
    """
    if isinstance(image_input, str):
        try:
            image = Image.open(image_input).convert("L")
        except FileNotFoundError:
            raise FileNotFoundError(f"Không tìm thấy file {image_input}!")
    elif isinstance(image_input, bytes):
        image = Image.open(io.BytesIO(image_input)).convert("L")
    else:
        raise ValueError("image_input phải là đường dẫn file (str) hoặc bytes!")
    
    image = image.resize((512, 512), Image.Resampling.LANCZOS)
    
    image_np = np.array(image)
    
    image_np = (image_np / 255.0) * 2048 - 1024
    
    image_tensor = torch.from_numpy(image_np).float().unsqueeze(0)

    return image_tensor

def process_xray_image(
        img_path: str,
        threshold: float = 0.5
    ):
    """
    Xử lý ảnh X-quang để phân loại bệnh lý và tạo heatmap Grad-CAM.
    
    Args:
        img_path (str): Đường dẫn tới ảnh X-quang.
        threshold (float): Xác suất tối thiểu
        
    Returns:
        tuple:
            - pathologies_above_threshold (list): Danh sách tuple (tên_bệnh_lý, xác_suất) cho các bệnh lý có xác suất > threshold.
            - gradcam_images (list): Danh sách dictionary chứa thông tin bệnh lý và ảnh heatmap.
    """
    try:
        model = get_model()
        model.eval()

        img = skimage.io.imread(img_path)

        if len(img.shape) > 2:
            img = img[:, :, 0]

        if len(img.shape) < 2:
            raise ValueError("Kích thước ảnh nhỏ hơn 2 chiều")

        img = img.astype(np.float32)

        img = (img / 255.0) * 2048 - 1024

        img = img[None, :, :]

        img_tensor = torch.from_numpy(img).float()

        transform = transforms.Compose([
            transforms.Resize((512, 512)),
            datasets.XRayCenterCrop(),
        ])

        img_tensor = transform(img_tensor)
        img_tensor = img_tensor.unsqueeze(0)
        img_tensor.requires_grad_(True)

        with torch.no_grad():
            preds = model(img_tensor).cpu()
            output = zip(model.pathologies, map(float, preds[0]))

        pathologies_above_threshold = [(k, v) for k, v in output if v > threshold]

        from .gradcam import compute_gradcam
        gradcam_images = []
        for pathology, prob in pathologies_above_threshold:
            target_class_idx = model.pathologies.index(pathology)
            heatmap = compute_gradcam(model, img_tensor, target_class_idx)
            gradcam_images.append({
                "pathology": pathology,
                "probability": prob,
                "heatmap": heatmap
            })

        return pathologies_above_threshold, gradcam_images

    except Exception as e:
        print(f"Lỗi khi xử lý ảnh: {str(e)}")
        return [], []