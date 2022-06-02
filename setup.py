from setuptools import find_packages, setup


if __name__ == "__main__":
    setup(
        name="eyesim",
        packages=find_packages(),
        install_requires=open("requirements.txt").read().strip().split("\n"),
        version="0.0.1",
        entry_points={
            "console_scripts": ["eyesim = eyesim.runner:run_cli"]
        }
    )
