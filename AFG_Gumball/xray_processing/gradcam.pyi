import torch
import numpy as np

def compute_gradcam(model: torch.nn.Module, img_tensor: torch.Tensor, target_class_idx: int) -> np.ndarray: ...