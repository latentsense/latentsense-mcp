from setuptools import setup, find_packages

setup(
    name="latentsense-mcp-server",
    version="1.0.0",
    description="MCP server for Latentsense API",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    install_requires=[
        "mcp>=1.0.0",
        "httpx>=0.25.0",
        "aiofiles>=23.0.0",
    ],
    entry_points={
        "console_scripts": [
            "latentsense-mcp=latentsense_server:main",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)