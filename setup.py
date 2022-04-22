from setuptools import setup

setup(name='django-flexible',
      version='2020.1',
      description='Flexible model package for django',
      url='http://github.com/cmberryau/django-flexible',
      author='Chris Berry',
      author_email='chris@chrisberry.com.au',
      license='MIT',
      packages=[
            'flexible',
            'flexible.migrations',
      ],
      install_requires=[
            'django==2.2.28',
            'django-polymorphic>=2.1.2',
            'django-crispy-forms>=1.7.2',
      ],
      include_package_data=True,
      zip_safe=False)
