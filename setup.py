from setuptools import setup, find_packages

setup(
    name="autoheal-ai",
    version="1.0.0",
    description="Hybrid statistical and AI-assisted data pipeline for anomaly detection and self-healing",
    author="Deepak, Rudra, Nikhil, Riddhi Garg",
    author_email="dg6663291@gmail.com",
    packages=find_packages(),
    install_requires=[
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "duckdb>=0.9.0",
        "requests>=2.31.0"
    ],
    entry_points={
        "console_scripts": [
            "autoheal=run_pipeline:main",
        ],
    },
    python_requires=">=3.10",
)
