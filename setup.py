from setuptools import setup, find_packages

setup(
    name='Modulize',
    version='1.0.0',
    url='https://github.com/jasonrute/modulize',
    author='Jason Rute',
    description='A Python decorator for converting a function into a module. It also includes tools for combining multiple Python files into one.',
    packages=find_packages(),
    scripts=[
        r'modulize\bin\combine_py_files.py',
        r'modulize\bin\modulization.py',
        r'modulize\bin\sync_combined_py_files.py'
    ]
)