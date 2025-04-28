import torch
import torch.nn.functional as F
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm

def find_target_layer(model):
    """
    Tìm lớp convolution cuối cùng trong mô hình DenseNet.
    
    Args:
        model: Mô hình PyTorch.
        
    Returns:
        Lớp convolution cuối cùng.
    """
    base_model = model.module if isinstance(model, torch.nn.DataParallel) else model
    try:
        dense_net = base_model.model
    except AttributeError:
        raise AttributeError("Không thể truy cập mô hình DenseNet.")
    try:
        dense_net = dense_net.module
    except AttributeError:
        pass
    try:
        backbone = dense_net.backbone
        conv_layers = []
        def find_conv_layers(module, prefix="backbone."):
            for name, child in module.named_children():
                if isinstance(child, torch.nn.Conv2d):
                    conv_layers.append((prefix + name, child))
                find_conv_layers(child, prefix + name + ".")
        find_conv_layers(backbone)
        if conv_layers:
            target_layer_name, target_layer = conv_layers[-1]
            return target_layer
        else:
            raise AttributeError("Không tìm thấy lớp convolution trong backbone.")
    except AttributeError:
        raise AttributeError("Không tìm thấy backbone trong mô hình.")

def compute_gradcam(model, img_tensor, target_class_idx):
    """
    Tính toán heatmap Grad-CAM cho một lớp bệnh lý cụ thể.
    
    Args:
        model: Mô hình PyTorch.
        img_tensor: Tensor ảnh đầu vào.
        target_class_idx: Chỉ số của lớp bệnh lý cần tính Grad-CAM.
        
    Returns:
        Ảnh heatmap kết hợp với ảnh gốc.
    """
    activation_list = []
    gradient_list = []

    def forward_hook(module, input, output):
        activation_list.append(output)

    def backward_hook(module, grad_in, grad_out):
        gradient_list.append(grad_out[0])

    target_layer = find_target_layer(model)
    target_layer.register_forward_hook(forward_hook)
    target_layer.register_backward_hook(backward_hook)

    output = model(img_tensor)
    model.zero_grad()
    output[:, target_class_idx].backward()

    if not activation_list or not gradient_list:
        raise RuntimeError("Không thu thập được activations hoặc gradients.")

    activations = activation_list[0]
    gradients = gradient_list[0]

    weights = torch.mean(gradients, dim=[2, 3], keepdim=True)
    gradcam = torch.mul(activations, weights).sum(dim=1, keepdim=True)
    gradcam = F.relu(gradcam)
    gradcam = F.interpolate(gradcam, size=img_tensor.shape[2:], mode='bilinear', align_corners=False)
    gradcam = gradcam.squeeze().detach().cpu().numpy()
    gradcam = (gradcam - gradcam.min()) / (gradcam.max() - gradcam.min() + 1e-8)

    img_np = img_tensor[0, 0].detach().cpu().numpy()
    heatmap_rgb = cm.jet(gradcam)[:, :, :3]
    overlay = (img_np - img_np.min()) / (img_np.max() - img_np.min())
    overlay = plt.cm.gray(overlay)[:, :, :3]
    alpha = 0.5
    combined = (1 - alpha) * overlay + alpha * heatmap_rgb
    combined = np.clip(combined, 0, 1)

    return combined