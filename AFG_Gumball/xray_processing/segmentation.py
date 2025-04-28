import torch
import torch.nn.functional as F
from .model_utils import get_segmentation_model
from .enums import BodyPart

def get_body_part_segment(image, part: BodyPart):
    """
    Trả về vùng phân đoạn của một bộ phận cơ thể cụ thể từ ảnh X-ray.

    Args:
        image: Ảnh X-ray đã được tiền xử lý. (Tensor, shape [1, H, W] hoặc [C, H, W])
        part: Bộ phận cơ thể cần lấy vùng phân đoạn (BodyPart enum).

    Returns:
        Tensor vùng phân đoạn của bộ phận được chỉ định, shape [512, 512].
    """
    _, h, w = image.shape
    if h != w:
        diff = abs(h - w)
        if h > w:
            left = diff // 2
            right = diff - left
            padding = (left, right, 0, 0)
        else:
            top = diff // 2
            bottom = diff - top
            padding = (0, 0, top, bottom)
        
        image = F.pad(image, padding, mode='constant', value=0)

    seg_model = get_segmentation_model()
    
    output = seg_model(image.unsqueeze(0))
    
    assert output.shape == (1, 14, 512, 512), f"Output shape không khớp: {output.shape}"
    
    part_index = part.value
    segment = output[0, part_index, :, :]
    
    return segment