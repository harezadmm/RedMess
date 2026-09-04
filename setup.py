from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text() if readme_file.exists() else ""

setup(
    name="redmess",
    version="1.0.0",
    author="harezadmm",
    author_email="security@redmess.dev",
    description="RedMess BRUTAL MOD - Unrestricted Offensive Security AI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/harezadmm/RedMess",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Information Technology",
        "Topic :: Security",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.9",
    install_requires=[
        "hermes-ai>=0.9.0",
        "anthropic>=0.40.0",
        "openai>=1.0.0",
        "requests>=2.31.0",
        "pyyaml>=6.0",
        "python-telegram-bot>=20.0",
    ],
    entry_points={
        "console_scripts": [
            "redmess=redmess.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "redmess": [
            "skills/**/*.md",
            "skills/**/*.py",
            "skills/**/*.sh",
        ],
    },
    keywords=[
        "offensive-security",
        "red-team",
        "penetration-testing",
        "exploit-development",
        "malware-analysis",
        "security-research",
        "ai-hacking",
    ],
    project_urls={
        "Bug Reports": "https://github.com/harezadmm/RedMess/issues",
        "Source": "https://github.com/harezadmm/RedMess",
        "Documentation": "https://github.com/harezadmm/RedMess/blob/main/README.md",
    },
)
