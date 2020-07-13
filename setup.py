import setuptools
import pathlib

here = pathlib.Path(__file__).parent.resolve()

long_description = (here / 'README.md').read_text(encoding='utf-8')
req = (here / 'requirements.txt').read_text(encoding='utf-8').splitlines()
req = [x.strip() for x in req if x.strip()]

setuptools.setup(
    name="nska_deserialize",
    version="1.0.0",
    author="Yogesh Khatri",
    author_email="yogesh@swiftforensics.com",
    description="Convert NSKeyedArchiver plist into a deserialized human readable plist",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ydkhatri/nska_deserialize",
    py_modules=["nska_deserialize", "ccl_bplist"],
    #packages=setuptools.find_packages(),
    install_requires=req,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    license="MIT License",
)