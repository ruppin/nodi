from setuptools import setup, find_packages

setup(
    name="nodi",
    packages=find_packages(exclude=["tests*", "docs*", "examples*"]),
    include_package_data=True,
)
