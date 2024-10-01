from setuptools import setup, find_packages

# Reading requirements.txt for dependencies
with open('requirements.txt') as f:
    required = f.read().splitlines()

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='freedata',
    version='0.16.7',
    packages=find_packages(where='.'),
    package_dir={'': '.'},
    install_requires=required,
    python_requires='>=3.9',
    author='DJ2LS',
    author_email='dj2ls@proton.me',
    description='INFO: THIS PACKAGE IS NOT YET WORKING - PLEASE USE THE OFFICIAL SCRIPT BASED SETUP',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/DJ2LS/FreeDATA',
    license='GPL3.0',
    entry_points={
        'console_scripts': [
            'freedata=freedata_server.server:main',  # Points to the main() function in server.py
        ],
    },
    include_package_data=True,  # Ensure non-python files are included if specified
    package_data={
        # Include all files under any directory within the 'freedata_server' package
        'freedata_server': ['lib/**/*'],  # Recursive include for all files in 'lib' and its subdirectories
        'freedata_gui': ['dist/**/*'],  # gui folder

    },
)
