from os import PathLike

import h5py
import numpy as np
from numpy import ndarray

from app.core.storage import user_storage


def save_analyzation_output(
    file_name: PathLike,
    pathologies: list[tuple[str, float]],
    gradcam_image: list[dict[str, str | float | ndarray]]
):
    with h5py.File(file_name, "w") as f:
        pathos = f.create_group("pathologies")
        pathos.create_dataset("name", data=np.array([name for name, _ in pathologies], dtype="S26"))
        pathos.create_dataset("probability", data=np.array([prob for _, prob in pathologies]))

        images = f.create_group("gradcam_image")
        for i, d in enumerate(gradcam_image):
            gradcam_i = images.create_group(str(i))
            gradcam_i.attrs["pathology"] = d["pathology"]
            gradcam_i.create_dataset("probability", data=d["probability"])
            gradcam_i.create_dataset("heatmap", data=d["heatmap"], compression="gzip")


def load_analyzation_output(
    file_name: PathLike
):
    with h5py.File(file_name, "r") as f:
        names = f["pathologies/name"][()].astype(str)
        probabilities = f["pathologies/probability"][()]
        pathologies = tuple(zip(names, probabilities))

        gradcam_images = tuple(
            {
                "pathology": group.attrs["pathology"],
                "probability": group["probability"][()],
                "heatmap": group["heatmap"][()]
            }
            for group in f["gradcam_image"].values()
        )

    return pathologies, gradcam_images


def save_heatmap(
    file_name: PathLike,
    heatmap: ndarray
):
    with h5py.File(file_name, "w") as f:
        f.create_dataset("heatmap", data=heatmap)


def load_heatmap(
    file_name: PathLike
) -> ndarray:
    with h5py.File(file_name, "r") as f:
        return f["heatmap"][()]