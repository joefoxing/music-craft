"""Setup configuration for lyrics-extraction library."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="lyrics-extraction",
    version="1.0.0",
    author="Music Cover AI Team",
    description="AI-powered lyrics extraction from audio using vocal separation and speech-to-text",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/lyric-cover-staging/lyrics-extraction-lib",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Topic :: Multimedia :: Sound/Audio",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.9",
    install_requires=[
        "faster-whisper>=1.1.0",
        "demucs>=4.0.1",
    ],
    extras_require={
        "gpu": [
            "torch>=2.0.0",
            "cuda-toolkit>=11.8",
        ],
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "black>=23.0",
            "pylint>=2.17",
            "mypy>=1.0",
        ]
    },
    entry_points={
        "console_scripts": [],
    },
)
