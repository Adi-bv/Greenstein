from setuptools import setup, find_packages

setup(
    name="greenstein_backend",
    version="0.1.0",
    packages=find_packages(where="backend"),
    package_dir={"": "backend"},
    install_requires=[
        "fastapi",
        "uvicorn[standard]",
        "sqlalchemy",
        "pydantic",
        "pydantic-settings",
        "openai",
        "python-dotenv",
        "sentence-transformers",
        "chromadb",
        "pypdf",
        "langchain",  
    ],
)
