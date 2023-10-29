from setuptools import find_packages, setup

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="dcmfile-parser",
    version="0.0.1",
    description="parser for dcm files",
    packages=find_packages(where="app"),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/y-menace/dcmfile-parser",
    author="MohitYadav",
    author_email="mohit.yadav.id.code.repos@gmail.com",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent",
    ],
    install_requires=["jinja2"],
    extras_require={
        "dev": ["pytest", "twine"],
    },
    python_requires=">=3.8",
)