from ..torchxrayvision import baseline_models

def get_model():
    """
    Tải mô hình DenseNet cho phân loại bệnh lý.
    
    Returns:
        Mô hình DenseNet đã được tải.
    """
    model = baseline_models.gumball.DenseNet()
    return model

def get_segmentation_model():
    """
    Tải mô hình PSPNet cho phân đoạn.
    
    Returns:
        Mô hình PSPNet đã được tải.
    """
    seg_model = baseline_models.gumball.PSPNet()
    return seg_model