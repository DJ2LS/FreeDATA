from setuptools import setup, find_packages

# Reading requirements.txt for dependencies
with open('requirements.txt') as f:
    required = f.read().splitlines()

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='freedata-server',
    version='0.15.3',
    packages=find_packages(where='.'),
    package_dir={'': '.'},
    install_requires=required,
    python_requires='>=3.9',
    author='DJ2LS',
    author_email='dj2ls@proton.me',
    description='A free, open-source, multi-platform application for sending files and messages, using the codec2 HF modems.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://freedata.app',
    license='GPL3.0',
    entry_points={
        'console_scripts': [
            'freedata-server=modem.server:main',  # Points to the main() function in server.py
        ],
    },
    include_package_data=True,  # Ensure non-python files are included if specified
    package_data={
        # Include all files under any directory within the 'modem' package
        'modem': ['lib/**/*'],  # Recursive include for all files in 'lib' and its subdirectories
    },
)
