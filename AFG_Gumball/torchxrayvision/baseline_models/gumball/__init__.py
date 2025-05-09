import sys
import os
import json
import pathlib
from collections import OrderedDict
from typing import List

import torch
import torch.nn as nn
import torchvision

from .. import *
from ... import utils
from .model import classifier
from .ptsemseg.pspnet import pspnet

thisfolder = os.path.dirname(__file__)
sys.path.insert(0, thisfolder)



def _convert_state_dict(state_dict):
    """Converts a state dict saved from a dataParallel module to normal 
       module state_dict inplace
       :param state_dict is the loaded DataParallel model_state
    """
    new_state_dict = OrderedDict()
    for k, v in state_dict.items():
        name = k[7:]  # remove `module.`
        new_state_dict[name] = v
    return new_state_dict


class PSPNet(nn.Module):
    """ChestX-Det Segmentation Model

    You can load pretrained anatomical segmentation models. `Demo Notebook <https://github.com/mlmed/torchxrayvision/blob/master/scripts/segmentation.ipynb>`_

    .. code-block:: python

        seg_model = baseline_models.chestx_det.PSPNet()
        output = seg_model(image)
        output.shape # [1, 14, 512, 512]
        seg_model.targets # ['Left Clavicle', 'Right Clavicle', 'Left Scapula', 'Right Scapula',
                          #  'Left Lung', 'Right Lung', 'Left Hilus Pulmonis', 'Right Hilus Pulmonis',
                          #  'Heart', 'Aorta', 'Facies Diaphragmatica', 'Mediastinum',  'Weasand', 'Spine']

    .. image:: _static/segmentation-pspnet.png

    https://github.com/Deepwise-AILab/ChestX-Det-Dataset

    .. code-block:: bibtex

        @article{Lian2021,
            title = {{A Structure-Aware Relation Network for Thoracic Diseases Detection and Segmentation}},
            author = {Lian, Jie and Liu, Jingyu and Zhang, Shu and Gao, Kai and Liu, Xiaoqing and Zhang, Dingwen and Yu, Yizhou},
            doi = {10.48550/arxiv.2104.10326},
            journal = {IEEE Transactions on Medical Imaging},
            url = {https://arxiv.org/abs/2104.10326},
            year = {2021}
        }

    params:
        cache_dir (str): Override directory used to store cached weights (default: ~/.torchxrayvision/)

    """

    targets: List[str] = [
        'Left Clavicle', 'Right Clavicle', 'Left Scapula',
        'Right Scapula', 'Left Lung', 'Right Lung',
        'Left Hilus Pulmonis', 'Right Hilus Pulmonis',
        'Heart', 'Aorta', 'Facies Diaphragmatica',
        'Mediastinum', 'Weasand', 'Spine',
    ]
    """"""

    def __init__(self, cache_dir:str = None):

        super(PSPNet, self).__init__()

        self.transform = torchvision.transforms.Compose([
            torchvision.transforms.Normalize(
                [0.485, 0.456, 0.406],
                [0.229, 0.224, 0.225]
            )
        ])

        model = pspnet(len(self.targets))

        url = "https://github.com/KienPC1234/AI-FOR-GOOD-2025-Gumball/releases/download/pthv2/pspnet_gumball_chestxray_best_model.pth"

        weights_filename = os.path.basename(url)
        if cache_dir is None:
            weights_storage_folder = utils.get_cache_dir()
        else:
            weights_storage_folder = cache_dir
        self.weights_filename_local = os.path.expanduser(os.path.join(weights_storage_folder, weights_filename))

        if not os.path.isfile(self.weights_filename_local):
            print("Downloading weights...")
            print("If this fails you can run `wget {} -O {}`".format(url, self.weights_filename_local))
            pathlib.Path(weights_storage_folder).mkdir(parents=True, exist_ok=True)
            utils.download(url, self.weights_filename_local)

        try:
            ckpt = torch.load(self.weights_filename_local, map_location="cpu")
            ckpt = _convert_state_dict(ckpt)
            model.load_state_dict(ckpt)
        except Exception as e:
            print("Loading failure. Check weights file:", self.weights_filename_local)
            raise e

        model.eval()
        self.model = model

    def forward(self, x):
        
        x = x.repeat(1, 3, 1, 1)
        
        x = utils.fix_resolution(x, 512, self)
        utils.warn_normalization(x)

        # expecting values between [-1024,1024]
        x = (x + 1024) / 2048

        # now between [0,1] for this model preprocessing
        x = self.transform(x)
        y = self.model(x)

        return y

    def __repr__(self):
        return "gumball-pspnet"


class DenseNet(nn.Module):
    """A model trained on the CheXpert data

    https://github.com/jfhealthcare/Chexpert
    Apache-2.0 License

    .. code-block:: bibtex

        @misc{ye2020weakly,
            title={Weakly Supervised Lesion Localization With Probabilistic-CAM Pooling},
            author={Wenwu Ye and Jin Yao and Hui Xue and Yi Li},
            year={2020},
            eprint={2005.14480},
            archivePrefix={arXiv},
            primaryClass={cs.CV}
        }

    """

    targets: List[str] = [
        'Cardiomegaly',
        'Edema',
        'Consolidation',
        'Atelectasis',
        'Effusion',
    ]
    """"""

    def __init__(self, apply_sigmoid=True):

        super(DenseNet, self).__init__()
        self.apply_sigmoid = apply_sigmoid

        with open(os.path.join(thisfolder, 'config/example.json')) as f:
            self.cfg = json.load(f)

        class Struct:
            def __init__(self, **entries):
                self.__dict__.update(entries)

        self.cfg = Struct(**self.cfg)

        model = classifier.Classifier(self.cfg)
        model = nn.DataParallel(model).eval()

        url = "https://github.com/KienPC1234/AI-FOR-GOOD-2025-Gumball/releases/download/pthv2/gumball-DenseNet121_pre_train.pth"

        weights_filename = os.path.basename(url)
        weights_storage_folder = os.path.expanduser(os.path.join("~", ".torchxrayvision", "models_data"))
        self.weights_filename_local = os.path.expanduser(os.path.join(weights_storage_folder, weights_filename))

        if not os.path.isfile(self.weights_filename_local):
            print("Downloading weights...")
            print("If this fails you can run `wget {} -O {}`".format(url, self.weights_filename_local))
            pathlib.Path(weights_storage_folder).mkdir(parents=True, exist_ok=True)
            utils.download(url, self.weights_filename_local)

        try:
            ckpt = torch.load(self.weights_filename_local, map_location="cpu")
            model.module.load_state_dict(ckpt)
        except Exception as e:
            print("Loading failure. Check weights file:", self.weights_filename_local)
            raise (e)

        self.model = model

        self.pathologies = self.targets

    def forward(self, x):
        x = x.repeat(1, 3, 1, 1)
        
        x = utils.fix_resolution(x, 512, self)
        utils.warn_normalization(x)

        # expecting values between [-1024,1024]
        x = x / 512
        # now between [-2,2] for this model

        y, _ = self.model(x)
        y = torch.cat(y, 1)

        if self.apply_sigmoid:
            y = torch.sigmoid(y)

        return y

    def __repr__(self):
        return "Gumball-DenseNet121"
