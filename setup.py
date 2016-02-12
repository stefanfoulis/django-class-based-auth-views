from setuptools import setup, find_packages

version = __import__('class_based_auth_views').__version__

setup(
    name="django-class-based-auth-views-jp",
    version=version,
    url='http://github.com/jperelli/django-class-based-auth-views',
    license='BSD',
    platforms=['OS Independent'],
    description="A reimplementation of django.contrib.auth.views as class based views.",
    long_description=open('README.rst').read(),
    author='Stefan Foulis',
    author_email='stefan@foulis.ch',
    maintainer='Julian Perelli',
    maintainer_email='jperelli@gmail.com',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
    ]
)
