#!/bin/bash

mkdir \stateFiles

cd \stateFiles

curl -O https://www2.census.gov/geo/tiger/GENZ2010/gz_2010_[01-02]_140_00_500k.zip
curl -O https://www2.census.gov/geo/tiger/GENZ2010/gz_2010_[04-06]_140_00_500k.zip
curl -O https://www2.census.gov/geo/tiger/GENZ2010/gz_2010_[08-13]_140_00_500k.zip
curl -O https://www2.census.gov/geo/tiger/GENZ2010/gz_2010_[15-42]_140_00_500k.zip
curl -O https://www2.census.gov/geo/tiger/GENZ2010/gz_2010_[44-51]_140_00_500k.zip
curl -O https://www2.census.gov/geo/tiger/GENZ2010/gz_2010_[53-56]_140_00_500k.zip

unzip \*.zip
