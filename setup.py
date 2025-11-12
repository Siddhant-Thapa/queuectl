from setuptools import setup, find_packages

setup(
    name="queuectl",
    version="1.0.0",
    author="Siddhant Thapa",
    author_email="thapasiddhant9@gmail.com", 
    description="CLI-based background job queue system with workers, retries, and DLQ",
    packages=find_packages(),
    install_requires=[],
    entry_points={
        "console_scripts": [
            "queuectl = queuectl.cli:main",  # making `queuectl` available as a shell command
        ],
    },
    python_requires=">=3.9",
)
