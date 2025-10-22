from setuptools import setup, find_packages

setup(
    name="investlib-data",
    version="0.1.0",
    description="Market data collection and investment record management",
    packages=find_packages(),
    install_requires=[
        "sqlalchemy>=2.0.0",
        "pandas>=2.1.0",
        "click>=8.1.0",
        "tushare>=1.2.85",
        "akshare>=1.11.0",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "investlib-data=investlib_data.cli:cli",
        ],
    },
    python_requires=">=3.10",
)
