# Python Wheel Files

This directory contains wheel (.whl) files for Python packages that can be installed offline.

## Included Packages

### FastAPI and Dependencies
- fastapi-0.115.12-py3-none-any.whl
- starlette-0.46.2-py3-none-any.whl
- pydantic-2.11.3-py3-none-any.whl
- pydantic_core-2.33.1-cp312-cp312-win_amd64.whl
- typing_extensions-4.13.2-py3-none-any.whl
- annotated_types-0.7.0-py3-none-any.whl
- anyio-4.9.0-py3-none-any.whl
- typing_inspection-0.4.0-py3-none-any.whl
- idna-3.10-py3-none-any.whl
- sniffio-1.3.1-py3-none-any.whl

### Scikit-image and Dependencies
- scikit_image-0.25.2-cp312-cp312-win_amd64.whl
- numpy-2.2.5-cp312-cp312-win_amd64.whl
- scipy-1.15.2-cp312-cp312-win_amd64.whl
- networkx-3.4.2-py3-none-any.whl
- pillow-11.2.1-cp312-cp312-win_amd64.whl
- imageio-2.37.0-py3-none-any.whl
- tifffile-2025.3.30-py3-none-any.whl
- packaging-25.0-py3-none-any.whl
- lazy_loader-0.4-py3-none-any.whl

## Installation Instructions

### Method 1: Using the Installation Script

Run the `install_wheels.bat` script from the parent directory:

```
install_wheels.bat
```

### Method 2: Manual Installation

To install a specific wheel file:

```
pip install wheels/package-name.whl
```

To install all wheel files with their dependencies:

```
pip install --no-index --find-links=wheels fastapi scikit-image
```

## Notes

- These wheel files are compatible with Python 3.12 on Windows 64-bit systems.
- For other platforms or Python versions, you'll need to download appropriate wheel files.
- The wheel files for FastAPI and scikit-image include all their dependencies.
