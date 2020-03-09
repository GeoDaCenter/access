import pandas as pd
import numpy as np
import boto3, json
from access.access import *

s3 = boto3.resource('s3')
bucketName = 'tract-access-csds'


def saveToS3(df, name, bucketName, useIndex = False):
    key = 'inputData/' + name + '.csv' 
    if useIndex:
        s3.Object(bucketName, key).put(Body = df.to_csv(index = True))
    else:
        s3.Object(bucketName, key).put(Body = df.to_csv(index = False))

def lambda_handler(event, context):

    #Parse recieved data

    print("Recieved data", event)
    print(type(event))

    data   = event['tract']
    uuid   = event['id']
    method = event['method']
    state  = event['state']
    county = event['county']
    city   = event['city']
    time_scale = int(event['time'])


    # Get the populations from S3
    extension ='PopulationData/UsPops.csv'
    popFile = s3.Object(bucketName, extension)
    pops = pd.read_csv(popFile.get()['Body'])
    pops.columns = ['geoid', 'demand']
    pops.demand = pops.demand.astype(int)
    pops.set_index('geoid', inplace = True)

    ## Now get doctors from the post request.
    docs = pd.DataFrame({'geoid'  : list(data.keys()), 
                         'supply' : list(data.values())})
    # print("input data")
    # print(list(data.values()))
    # print(docs)
    docs.geoid  = docs.geoid. astype(int)
    docs.supply = docs.supply.astype(int)
    # print(docs)
    docs = docs[docs['supply'] != 0]
    docs.set_index('geoid', inplace = True)
    # print(docs)


    all_tracts = pd.Series(sorted(list(set(pops.index) | set(docs.index))))

    if city != '':

        print(city)
        cityFips = s3.Object(bucketName, 'FIPSdata/cityCodes.json')
        cityCodes = json.load(cityFips.get()['Body'])
        tracts = cityCodes[city]

    elif county != '':

        print(county)
        all_tracts = all_tracts[all_tracts // 1000000 == int(county)]
        tracts = list(all_tracts)

    else:

        print(state)
        all_tracts = all_tracts[all_tracts // 1000000000 == int(state)]
        tracts = list(all_tracts)


    # print("DOCS :::")
    # print(docs.head())

        
    # print("TRACTS :::")
    # print(tracts)
    pops.drop(pops.loc[~pops.index.isin(tracts)].index, inplace = True)
    docs.drop(docs.loc[~docs.index.isin(tracts)].index, inplace = True)


    # print("DOCS :::")
    # print(docs.head())

    all = []
    travel = pd.DataFrame()

    #Getting list of counties
    counties = set((pops.index // 1000000).astype(str).str.zfill(5))
    for county in counties:

        extension = 'times/pgr/' + county[0:2] + '/' + county[2:5] + '.csv'
        all.append(extension)
        timesFile = s3.Object(bucketName, extension)
        try:
            time = pd.read_csv(timesFile.get()['Body'])
            time = time.drop(time.loc[~time.origin.isin(tracts)].index)
            time = time.drop(time.loc[~time.destination.isin(tracts)].index)
            travel = travel.append(time,ignore_index=True,sort=True)
        except:
            print("The following county doesn't exist: ", county)


    travel.columns = ['cost', 'dest', 'origin']
    # travel.dest = pd.to_numeric(travel.dest)

    validOrigins = list(pops.index)
    additionalSelfTimes = pd.DataFrame({'origin': validOrigins, 'dest': validOrigins, 'cost': [0] * len(validOrigins)})
    travel = pd.concat([travel, additionalSelfTimes], ignore_index = True, sort=True)

    
    # print(travel.head())
    # print(docs.head())
    # print(pops.head())
    saveToS3(travel, 'ttime', bucketName)
    saveToS3(docs,   'docs',  bucketName, True)
    saveToS3(pops,   'pops',  bucketName, True)

    tester = access(demand_df = pops, demand_value = 'demand', 
                    supply_df = docs, supply_value = 'supply',
                    demand_index = True, supply_index = True,
                    cost_df = travel, cost_origin = 'origin', cost_dest = 'dest', cost_name = 'cost',
                    neighbor_cost_df = travel, neighbor_cost_origin = 'dest', 
                    neighbor_cost_dest = 'origin', neighbor_cost_name = 'cost')
    
    if   method == 'FCA':
        data = tester.fca_ratio(max_cost = time_scale, normalize = True)
    elif method == "Catch":
        tri = weights.step_fn({(i+1)*10*time_scale / 60 : round(1 - i/6, 2) for i in range(6)})
        data = tester.weighted_catchment(max_cost = 60, normalize = True, weight_fn = tri)
    elif method == '2SFCA':
        data = tester.two_stage_fca(max_cost = time_scale, normalize = True)
    elif method == 'E2SFCA':
        wfn = weights.step_fn({k * 20 * time_scale / 60 : v 
                               for k, v in {1 : 1, 2 : 0.68, 3 : 0.22}.items()})
        data = tester.enhanced_two_stage_fca(max_cost = time_scale, normalize = True, weight_fn = wfn)
    elif method == '3SFCA':
        wfn = weights.step_fn({k * 10 * time_scale / 60 : v
                               for k, v in {1 : 0.962, 2 : 0.704, 3 : 0.377, 6 : 0.042}.items()})
        data = tester.three_stage_fca(max_cost = time_scale, normalize = True, weight_fn = wfn)
    else:
        data = tester.raam(tau = time_scale, verbose = True)

    
    # print(data.head())

    s3Objs = []
    key = 'tempAccessData/' + uuid + '.csv'
    s3.Object(bucketName, key).put(Body = data.to_csv(index = True))
    s3Objs.append('https://' + bucketName + '.s3.us-east-1.amazonaws.com/' + key)
    return {
        'statusCode': 200,
        'body': json.dumps(str(s3Objs))
    }

