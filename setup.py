import setuptools

with open("README.md", "r") as f:
    long_description = f.read()

setuptools.setup(
    name="vanguard-api",
    version="0.1.9",
    author="MaxxRK",
    author_email="maxxrk@pm.me",
    description="An unofficial API for Vanguard Invest",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    url="https://github.com/MaxxRK/vanguard-api",
    download_url="https://github.com/MaxxRK/vanguard-api/archive/refs/tags/v0.1.9.tar.gz",
    keywords=["VANGUARD", "API"],
    install_requires=["playwright", "playwright-stealth"],
    packages=["vanguard"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Internet :: WWW/HTTP :: Session",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
