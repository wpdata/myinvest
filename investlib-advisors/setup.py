from setuptools import setup, find_packages

setup(
    name="investlib-advisors",
    version="0.1.0",
    description="AI advisor implementations with versioned prompts",
    packages=find_packages(),
    install_requires=[
        "click>=8.1.0",
    ],
    entry_points={
        "console_scripts": [
            "investlib-advisors=investlib_advisors.cli:cli",
        ],
    },
    python_requires=">=3.10",
)
