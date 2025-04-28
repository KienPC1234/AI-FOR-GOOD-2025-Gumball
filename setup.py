from setuptools import setup, find_packages

with open("README_Pak.md", "r", encoding="utf-16") as fh:
    long_description = fh.read()

setup(
    name="AFG_Gumball",
    version="0.1.0",
    description="A Python package for processing medical X-ray images and AI-based diagnosis",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="KienTF",
    author_email="kienpc872009@gmail.com",
    url="https://github.com/KienPC1234/AI-FOR-GOOD-2025-Gumball", 
    packages=find_packages(include=["AFG_Gumball", "AFG_Gumball.*"]),
    install_requires=[
        "google-genai",
        "torch>=1.0.0",
        "pydicom>=2.0.0",
        "torchvision>=0.5.0",
        "scikit-image>=0.16.0",
        "tqdm>=4.0.0",
        "numpy>=1.0.0",
        "pandas>=1.0.0",
        "requests>=1.0.0",
        "pillow>=5.3.0",
        "imageio>=2.0.0",
        "python-dotenv>=0.10.0",
        "matplotlib>=3.0.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    include_package_data=True,
)