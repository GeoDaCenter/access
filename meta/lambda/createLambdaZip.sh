#!/bin/bash

cd lambdadata

git clone https://github.com/JamesSaxon/access.git

pip install -t . pandas

rm -r *.dist-info __pycache__

rm -r pandas numpy *.dist-info

wget https://files.pythonhosted.org/packages/e6/de/a0d3defd8f338eaf53ef716e40ef6d6c277c35d50e09b586e170169cdf0d/pandas-0.24.1-cp36-cp36m-manylinux1_x86_64.whl

wget https://files.pythonhosted.org/packages/f5/bf/4981bcbee43934f0adb8f764a1e70ab0ee5a448f6505bd04a87a2fda2a8b/numpy-1.16.1-cp36-cp36m-manylinux1_x86_64.whl

unzip numpy-1.16.1-cp36-cp36m-manylinux1_x86_64.whl

unzip pandas-0.24.1-cp36-cp36m-manylinux1_x86_64.whl

pip install -t . pytz

rm -r *.whl *.dist-info __pycache__

zip -r zip.zip .
