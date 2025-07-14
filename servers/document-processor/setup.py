"""
Setup script for Document Processor CLI.

This makes the document processor installable as a CLI tool using pip or pipx.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

# Read requirements
requirements = []
with open("requirements.txt") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="mdproc",
    version="1.0.0",
    description="Convert markdown documents to PDF, HTML, DOCX, and TXT formats",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Markdown Processor Team",
    author_email="team@mdproc.dev",
    url="https://github.com/mdproc/markdown-processor",
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "mdproc=cli.main:app",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Documentation",
        "Topic :: Text Processing :: Markup",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
    keywords="markdown pdf html docx txt converter cli document processing",
    project_urls={
        "Bug Reports": "https://github.com/docproc/document-processor/issues",
        "Source": "https://github.com/docproc/document-processor",
        "Documentation": "https://github.com/docproc/document-processor/blob/main/README.md",
    },
)
