from setuptools import setup, find_packages

setup(
    name="new_data_assistant_project",
    version="0.1.0",
    packages=find_packages(include=['new_data_assistant_project', 'new_data_assistant_project.*']),
    install_requires=[
        'anthropic',
        'pandas',
        'numpy',
    ],
    python_requires='>=3.8',
) 