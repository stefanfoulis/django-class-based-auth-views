from setuptools import setup, find_packages

version = __import__('class_based_auth_views').__version__

setup(
    name="django-class-based-auth-views",
    version=version,
    url='http://github.com/stefanfoulis/django-class-based-auth-views',
    license='BSD',
    platforms=['OS Independent'],
    description="A reimplementation of django.contrib.auth.views as class based views.",
    long_description=open('README.rst').read(),
    author='Stefan Foulis',
    author_email='stefan.foulis@gmail.com',
    maintainer='Stefan Foulis',
    maintainer_email='stefan.foulis@gmail.com',
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
