import setuptools

with open("README.md", encoding="utf-8") as f:
    readme = f.read()

setuptools.setup(
    name="tglogging-black",
    version="0.1.6",
    author="eyMarv",
    description="A python package to stream your app logs to a telegram chat in realtime.",
    long_description=readme,
    long_description_content_type="text/markdown",
    project_urls={
        "Tracker": "https://github.com/eyMarv/tglogging/issues",
        "Source": "https://github.com/eyMarv/tglogging",
    },
    license="MIT",
    url="https://github.com/eyMarv/tglogging",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    packages=setuptools.find_packages(),
    python_requires=">=3.8",
    install_requires=["aiohttp>=3.9.3"],
)
