@echo off
REM Script to install wheel files
REM Run this script on the target machine where you want to install the packages

echo Installing wheel files from the wheels directory...
pip install --no-index --find-links=wheels fastapi scikit-image

echo Installation complete!
