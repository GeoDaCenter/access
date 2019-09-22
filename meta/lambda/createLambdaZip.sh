#!/bin/bash

cd lambdadata

rm -rf access/ numpy/ pandas/ pytz/ six.py dateutil/ bin/
rm -r *.dist-info __pycache__

git clone https://github.com/JamesSaxon/access.git
rm -rf access/.git

# NB that you should do this in a python 3.7 environment, 
# or at any rate, one that matches the one used for the AWS fn

pip install -t . pandas
rm -r *.dist-info __pycache__

zip -r zip.zip .
mv zip.zip ../

cd ../

