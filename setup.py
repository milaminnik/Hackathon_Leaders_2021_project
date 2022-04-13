from setuptools import setup

with open('requirements.txt') as f:
    required = f.read().splitlines()  
      
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='anonymizer',
    version='1.0',
    author='INID',
    author_email='m.vedenkov@data-in.ru',
    description="A full name anonimizer for office documents.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/CAG-ru/anonymizer',
    #project_urls={
    #    "Bug Tracker": "https://github.com/CAG-ru/anonymizer/issues"
    #},
    license='Apache',
    include_package_data=True,
    package_data={'anonymizer': ['anonymizer/*.json', '*.json']},
    packages=['anonymizer'],
    install_requires=required, #install_requires=['requests', 'pandas'],
)

#import stanza
#stanza.download('ru')
