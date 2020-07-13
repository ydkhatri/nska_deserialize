import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("requirements.txt", "r") as fh:
    req = [x for x in fh.read().splitlines() if x]

setuptools.setup(
    name="nska_deserialize",
    version="1.0.0",
    author="Yogesh Khatri",
    author_email="yogesh@swiftforensics.com",
    description="Convert NSKeyedArchiver plists into a deserialized human readable plist",
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
)