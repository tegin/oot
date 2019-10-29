from setuptools import find_packages, setup

from oot.constants import __version__ as version

try:
    # For pip >= 10.
    from pip._internal.req import parse_requirements
    from pip._internal.download import PipSession
except ImportError:
    # For pip <= 9.0.3.
    from pip.req import parse_requirements
    from pip.download import PipSession


install_reqs = parse_requirements("requirements.txt", session=PipSession())

install_requires = [str(ir.req) for ir in install_reqs]

setup(
    name="Oot",
    version=version,
    description="Package for management of odoo iot devices",
    long_description="Package for management of odoo iot devices",
    author="Enric Tobella Alomar",
    author_email="etobella@creublanca.es",
    url="http://github.com/tegin/oot",
    install_requires=install_requires,
    entry_points={},
    packages=find_packages(),
    package_data={"oot": ["static/*.css", "templates/*.html", "static/*.woff2"]},
    license="BSD",
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    zip_safe=False,
)
