"""
Django BulkSMS BD - Setup Configuration
"""

from setuptools import setup, find_packages
import os
# Read README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="django-bulksms-bd",
    version="0.1.0",
    author="Sharfuddin Shawon",
    author_email="sharf@shawon.me",
    description="Django package for integrating with BulkSMSBD.net API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sharf-shawon/django-bulksms-bd",
    project_urls={
        "Bug Tracker": "https://github.com/sharf-shawon/django-bulksms-bd/issues",
        "Documentation": "https://github.com/sharf-shawon/django-bulksms-bd",
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Framework :: Django",
        "Framework :: Django :: 3.2",
        "Framework :: Django :: 4.0",
        "Framework :: Django :: 4.1",
        "Framework :: Django :: 4.2",
        "Framework :: Django :: 5.0",
        "Topic :: Communications",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=requirements,
    include_package_data=True,
    zip_safe=False,
    keywords="django sms bulksms bangladesh api",
    test_suite="tests",
)
