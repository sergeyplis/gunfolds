from setuptools import setup

with open('README.md') as description:
    description = description.read()

execfile('gunfolds/version.py') # Acquire version constants.

# Define some package entry points. These will be command-line scripts that get
# installed into the user's PATH
epoints = """
[console_scripts]
"""

install_requires = ['networkx', 'python-igraph', 'scipy', 'numpy',
                    'statsmodels', 'sympy', 'seaborn', 'pandas',
                    'matplotlib', 'progressbar', 'gmpy', 'ipdb']

tests_require = install_requires

setup(
    name='gunfolds',
    description='Tools to explore dynamic causal graphs in the case of undersampled data',
    version=__version__,
    author='Sergey Plis, Cynthia Freeman, Ian Beaver',
    author_email='splis@mrn.org',
    license='GPL',
    long_description=description,
    include_package_data=True, # Include files listed in MANIFEST.in
    packages=['gunfolds'], # Sub-packages must be explicitly listed.
    #entry_points=epoints,
    install_requires=install_requires, # List of dependencies.
    test_suite='tests.tests',
    tests_require=tests_require,
    zip_safe=False) # Override annoying default behavior of easy_install.
