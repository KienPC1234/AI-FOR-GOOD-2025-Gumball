import torch
from .enums import BodyPart

def get_body_part_segment(image: torch.Tensor, part: BodyPart) -> torch.Tensor: ...