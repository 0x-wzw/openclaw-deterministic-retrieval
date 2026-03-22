from setuptools import setup, find_packages

setup(
    name="openclaw-deterministic-retrieval",
    version="0.1.0",
    description="Deterministic retrieval mode for OpenClaw - predictable and debuggable file/memory retrieval",
    author="0x-wzw",
    url="https://github.com/0x-wzw/openclaw-deterministic-retrieval",
    py_modules=["deterministic_retrieval", "cli"],
    entry_points={
        "console_scripts": [
            "openclaw-retrieve=cli:main",
        ],
    },
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
    ],
    keywords="openclaw retrieval deterministic semantic hybrid memory",
)