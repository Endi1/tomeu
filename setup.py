from setuptools import setup

setup(
    name="Tomeu",
    version="0.0.1",
    author="Endi Sukaj",
    author_email="endisukaj@gmail.com",
    packages=["tomeu"],
    include_package_data=True,
    package_data={'': ['tomeu/setup_files/*.html']},
    entry_points={"console_scripts": [
        "tomeu=tomeu.app:main"
    ]},

    install_requires=[
        "feedparser"
    ]
)
