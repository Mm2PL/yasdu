import setuptools

with open('README.md', 'r') as f:
    long_description = f.read()

setuptools.setup(
    name='yasdu',
    version='1.0.0',
    author='Mm2PL',
    author_email='mm2pl+yasdu@o2.pl',
    description='Yet another stack/session dumper utility',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/mm2pl/yasdu',
    packages=setuptools.find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Debuggers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities'
    ],
    python_requires='>=3.6',
    entry_points={
        'console_scripts': [
            'yasdu=yasdu.__main__:_main'
        ]
    }
)
