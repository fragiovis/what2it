from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="smart-fridge-recommender",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Sistema di raccomandazione intelligente per ricette basate sul contenuto del frigorifero",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/smart-fridge-recommender",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "jupyter>=1.0.0",
            "notebook>=6.4.0",
        ],
        "gpu": [
            "tensorflow-gpu>=2.8.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "smart-fridge=src.ui.cli.main:main",
            "smart-fridge-server=src.api.server:main",
        ],
    },
)