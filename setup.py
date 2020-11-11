from setuptools import setup, find_packages

setup(name = "statusline",
        author = "Aaron Moore",
        description = "display directory and repository stats for statusline",
        packages = ["statusline"],
        entry_points = {
            "console_scripts": [
                "statusline = statusline.__main__:main"
            ]
        },
        install_requires = ["ansi"]
        )
