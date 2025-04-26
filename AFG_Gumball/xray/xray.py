import skimage.io
import torch
import torch.nn.functional as F
import torchvision.transforms as transforms
import torchxrayvision as xrv
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm

def process_xray_image(img_path):
    """
    Xử lý ảnh X-quang để phân loại bệnh lý và tạo heatmap Grad-CAM.
    
    Args:
        img_path (str): Đường dẫn tới ảnh X-quang.
        
    Returns:
        tuple:
            - pathologies_above_0_5 (list): Danh sách tuple (tên_bệnh_lý, xác_suất) cho các bệnh lý có xác suất > 0.5.
            - gradcam_images (list): Danh sách dictionary chứa thông tin bệnh lý và ảnh heatmap.
    """
    try:
        # Tải mô hình
        model = xrv.baseline_models.jfhealthcare.DenseNet()
        model.eval()

        # Tải và tiền xử lý ảnh
        img = skimage.io.imread(img_path)
        img = xrv.datasets.normalize(img, 255)
        if len(img.shape) > 2:
            img = img[:, :, 0]
        if len(img.shape) < 2:
            raise ValueError("Kích thước ảnh nhỏ hơn 2 chiều")
        img = img[None, :, :]  # Shape: [1, H, W]

        # Chuyển thành tensor và áp dụng biến đổi
        img_tensor = torch.from_numpy(img).float()
        transform = transforms.Compose([
            transforms.Resize((512, 512)),  # Độ phân giải gốc
            xrv.datasets.XRayCenterCrop(),
        ])
        img_tensor = transform(img_tensor)
        img_tensor = img_tensor.unsqueeze(0)  # Shape: [1, 1, 512, 512]
        img_tensor.requires_grad_(True)

        # Phân loại
        with torch.no_grad():
            preds = model(img_tensor).cpu()
            output = {k: float(v) for k, v in zip(model.pathologies, preds[0])}

        # Lọc bệnh lý có xác suất > 0.5
        pathologies_above_0_5 = [(k, v) for k, v in output.items() if v > 0.5]

        # Tìm lớp mục tiêu cho Grad-CAM
        def find_target_layer(model):
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

        # Triển khai Grad-CAM
        def compute_gradcam(model, img_tensor, target_class_idx):
            activation_list = []
            gradient_list = []

            def forward_hook(module, input, output):
                nonlocal activation_list
                activation_list.append(output)

            def backward_hook(module, grad_in, grad_out):
                nonlocal gradient_list
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

            # Tạo ảnh heatmap phủ lên ảnh gốc
            img_np = img_tensor[0, 0].detach().cpu().numpy()
            heatmap_rgb = cm.jet(gradcam)[:, :, :3]  # Chuyển heatmap sang RGB
            overlay = (img_np - img_np.min()) / (img_np.max() - img_np.min())  # Chuẩn hóa ảnh gốc
            overlay = plt.cm.gray(overlay)[:, :, :3]  # Chuyển ảnh gốc sang RGB
            alpha = 0.5
            combined = (1 - alpha) * overlay + alpha * heatmap_rgb
            combined = np.clip(combined, 0, 1)

            return combined

        # Tạo heatmap Grad-CAM cho các bệnh lý
        gradcam_images = []
        for pathology, prob in pathologies_above_0_5:
            target_class_idx = model.pathologies.index(pathology)
            heatmap = compute_gradcam(model, img_tensor, target_class_idx)
            gradcam_images.append({
                "pathology": pathology,
                "probability": prob,
                "heatmap": heatmap
            })

        return pathologies_above_0_5, gradcam_images

    except Exception as e:
        print(f"Lỗi khi xử lý ảnh: {str(e)}")
        return [], []

