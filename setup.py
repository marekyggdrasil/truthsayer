import setuptools

setuptools.setup(
    name='truthsayer',
    version='0.2.5',
    packages=['truthsayer',],
    license='MIT',
    description = 'Visualizes and manages Dune the Board Game state',
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    author = 'Marek Narozniak',
    author_email = 'marek.yggdrasil@gmail.com',
    install_requires=['pillow', 'qrcode', 'beautifulsoup4==4.8.1', 'simpleai', 'brackette'],
    url = 'https://github.com/marekyggdrasil/truthsayer',
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 2",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    include_package_data=True,
    package_data = {
        # If any package contains *.txt or *.rst files, include them:
        '': ['assets/__init__.py', 'assets/json_files/__init__.py', 'assets/*.png', 'assets/*.ttf', 'assets/*.json', 'assets/json_files/*.json'],
    }
)
