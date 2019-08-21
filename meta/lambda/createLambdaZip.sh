#!/bin/bash

pip install -t . pandas

rm -r *.dist-info __pycache__

rm -r pandas numpy *.dist-info

wget https://files.pythonhosted.org/packages/1d/9a/7eb9952f4b4d73fbd75ad1d5d6112f407e695957444cb695cbb3cdab918a/pandas-0.25.0-cp36-cp36m-manylinux1_x86_64.whl

wget https://files.pythonhosted.org/packages/19/b9/bda9781f0a74b90ebd2e046fde1196182900bd4a8e1ea503d3ffebc50e7c/numpy-1.17.0-cp36-cp36m-manylinux1_x86_64.whl

unzip numpy-1.17.0-cp36-cp36m-manylinux1_x86_64.whl

unzip pandas-0.25.0-cp36-cp36m-manylinux1_x86_64.whl

pip install -t . pytz

rm -r *.whl *.dist-info __pycache__

zip -r zip.zip .
