from setuptools import setup, find_packages

setup(
    name="teacherspet",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "ElevenLabs",
        "dotenv",
        "PySide6",
        "ultralytics",
        "collections",
        "pyautogui",

        "opencv-python"

        "win32gui",
        "win32con"

    ],
)