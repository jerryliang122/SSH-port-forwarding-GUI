#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
安装脚本
"""

from setuptools import setup, find_packages

setup(
    name="linux-ssh-port-forwarding",
    version="1.0.0",
    description="Linux SSH 端口转发工具",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/linux-ssh-port-forwarding",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "PyQt5>=5.15.0",
        "paramiko>=2.7.2",
        "cryptography>=3.4.0",
    ],
    entry_points={
        "console_scripts": [
            "ssh-port-forwarding=src.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: X11 Applications :: Qt",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: System :: Networking",
        "Topic :: Utilities",
    ],
    python_requires=">=3.7",
)