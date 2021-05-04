import setuptools

setuptools.setup(
    name='arrakis',
    version='0.0.1',
    packages=['arrakis',],
    license='MIT',
    description = 'Visualizes Dune the Board Game state',
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    author = 'Marek Narozniak',
    author_email = '',
    install_requires=['pillow', 'qrcode'],
    url = 'https://github.com/marekyggdrasil/arrakis',
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 2",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    include_package_data=True,
    package_data = {
        # If any package contains *.txt or *.rst files, include them:
        '': ['assets/__init__.py', 'assets/*.png', 'assets/*.ttf'],
    }
)
