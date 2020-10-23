import setuptools


def readme():
    with open('README.md') as f:
        return f.read()


def requirements():
    with open('requirements.txt') as f:
        return f.read().splitlines()


setuptools.setup(
    name='credentialdigger',
    version='2.0.2',
    author='SAP SE',
    maintainer='Marco Rosa, Slim Trabelsi',
    maintainer_email='marco.rosa@sap.com, slim.trabelsi@sap.com',
    description='Credential Digger',
    install_requires=requirements(),
    long_description=readme(),
    long_description_content_type='text/markdown',
    url='https://github.com/SAP/credential-digger',
    packages=setuptools.find_packages(),
    include_package_data=True,
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.5, <3.8',
)
