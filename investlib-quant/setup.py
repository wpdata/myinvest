from setuptools import setup, find_packages

setup(
    name="investlib-quant",
    version="0.1.0",
    description="Quantitative strategy analysis and signal generation",
    packages=find_packages(),
    install_requires=[
        "pandas>=2.1.0",
        "pandas-ta>=0.3.14b",
        "numpy>=1.24.0",
        "click>=8.1.0",
    ],
    entry_points={
        "console_scripts": [
            "investlib-quant=investlib_quant.cli:cli",
        ],
    },
    python_requires=">=3.10",
)
