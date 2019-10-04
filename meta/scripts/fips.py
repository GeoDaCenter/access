#!/usr/bin/env python 

import pandas as pd

import psycopg2
from netrc import netrc
user, acct, passwd = netrc().authenticators("harris")

cen_con = psycopg2.connect(database = "census", user = user, password = passwd,
                           host = "saxon.harris.uchicago.edu", port = 5432)

df = pd.read_sql("select fips, name from states where fips < 57 order by fips;", con = cen_con)
df.to_csv("state_fips.csv", index = False)

df = pd.read_sql("select geoid::INT fips, name from counties_2010 where state < 57 order by fips;", con = cen_con)
df.to_csv("county_fips.csv", index = False)
