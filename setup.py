from setuptools import setup, find_packages

setup(
    name="teacherspet",
    version="0.0.0",
    packages=find_packages(),
    install_requires=[
        "ElevenLabs",
        "dotenv",
        "PySide6",
        "ultralytics",
        "collections",
        "pyautogui",
        "pydub",
        "opencv-python"


    ],
)