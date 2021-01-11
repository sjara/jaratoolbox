from setuptools import setup, find_packages

setup(
    name='jaratoolbox',
    version='2.0',
    author='Santiago Jaramillo',
    author_email='sjara@uoregon.edu',
    description='Data analysis package for the Jaramillo lab.',
    packages=find_packages(exclude=[]),
    long_description=open('README.md').read(),
    long_description_content_type='text/x-rst; charset=UTF-8',
    install_requires=[]
)


