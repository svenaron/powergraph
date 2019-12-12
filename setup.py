import setuptools
import os

def get_long_desc():
    fp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "README.md")
    with open(fp, "r") as fh:
        return fh.read()

setuptools.setup(
    name = "wattalizer",
    version = "0.0.1",
    author = "Sven Westergren",
    author_email = "sven.westergren@gmail.com",
    description = "Plot GoldenCheetah data for sprint cyclists",
    long_description = get_long_desc(),
    long_description_content_type = "text/markdown",
    url = "https://github.com/svenaron/wattalizer",
    packages = setuptools.find_packages(),
    classifiers = [
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires = ['pandas', 'plotly', 'numpy', 'bottle'],
    python_requires = '>=3.6',
)
