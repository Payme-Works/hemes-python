from setuptools import (setup, find_packages)

setup(
    name="hermes",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "pylint",
        "requests",
        "websocket-client==0.56"
    ],
    include_package_data=True,
    description="SDK for communication with IQ Option",
    long_description="Hermes is a (non-official) SDK for communication with IQ Option",
    url="https://github.com/PaymeTrade/hermes",
    author="André 'Dezzy' <@andredezzy>",
    zip_safe=False
)
