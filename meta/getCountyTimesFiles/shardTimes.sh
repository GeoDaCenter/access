#!/bin/bash


# Downloading times file
wget https://s3-eu-west-1.amazonaws.com/pfigshare-u-files/13616243/times.csv.bz2

#Unzipping times file
bzip2 -d times.csv.bz24

#Make a directory to store indiviual sharded files
mkdir -p shardedTimes;

#Loop through times file
sed 1d times.csv | while IFS=',' read origin destination travelTime
do

origin_length=${#origin}

#Since some state codes are 2 digits and some are one it is necessary to check the length.
if [ $origin_length -eq 10 ]
then
    mkdir -p shardedTimes/${origin:0:1}/${origin:1:3};
    echo "$destination, $travelTime" >> shardedTimes/${origin:0:1}/${origin:1:3}/${origin: -6}.csv
else
    mkdir -p shardedTimes/${origin:0:2}/${origin:2:3};
    echo "$destination, $travelTime" >> shardedTimes/${origin:0:2}/${origin:2:3}/${origin: -6}.csv
fi


done

