from setuptools import setup

setup(
    name="Tomeu",
    version="0.0.1",
    author="Endi Sukaj",
    author_email="endisukaj@gmail.com",
    packages=["tomeu"],
    entry_points={"console_scripts": [
        "tomeu=tomeu.app:main"
    ]},

    install_requires=[
        "feedparser"
    ]
)
