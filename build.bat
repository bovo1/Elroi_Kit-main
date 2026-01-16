@echo off
chcp 65001
rmdir /s /q dist

call conda activate ElroiKit

@REM Obfuscation & Packaging
pyarmor pack -s .\ElroiKit.spec .\src\ElroiKit.py --clean
