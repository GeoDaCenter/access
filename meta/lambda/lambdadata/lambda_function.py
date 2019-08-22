import pandas as pd
import numpy as np
import boto3, json
from access.access import *

s3 = boto3.resource('s3')
bucketName = 'tractaccessinfo'

def raamPrep(pops, docs):
    pops.demand = pd.to_numeric(pops.demand)
    return pops, docs


def FCAPrep(docs, pops):
    docs = docs[docs['supply'] != 0]
    docs.set_index('geoid', inplace = True)
    pops.set_index('geoid', inplace = True)
    return docs, pops

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
    try:
        params = json.loads(event['body'])
        data = params['tract']
        uuid = params['id']
        method = params['method']
        location = params['location']
        state = params['state']
    except:
        data = event['tract']
        uuid = event['id']
        method = event['method']
        location = event['location']
        state = event['state']


    if state != '':
        stateFips = s3.Object(bucketName, 'FIPSdata/stateCodes.json')
        stateCodes = json.load(stateFips.get()['Body'])
        stateCode = stateCodes[state]

         #Get population data
        extension ='PopulationData/UsPops.csv'
        popFile = s3.Object(bucketName, extension)
        pops = pd.read_csv(popFile.get()['Body'])
        pdtracts = pops.geoid

        if location != 'All Counties':

            countyFips = s3.Object(bucketName, 'FIPSdata/countyCodes.json')
            countyCodes = json.load(countyFips.get()['Body'])
            locationCode = stateCode + countyCodes[stateCode][location]

            pdtracts = pdtracts[pdtracts//1000000 == int(locationCode)]
            tracts = list(pdtracts)

        else:
            pdtracts = pdtracts[pdtracts//1000000000 == int(stateCode)]
            tracts = list(pdtracts)

        

    else:
        cityFips = s3.Object(bucketName, 'FIPSdata/cityCodes.JSON')
        cityCodes = json.load(cityFips.get()['Body'])
        tracts = cityCodes[location]

        extension ='PopulationData/UsPops.csv'
        popFile = s3.Object(bucketName, extension)
        pops = pd.read_csv(popFile.get()['Body'])
        pdtracts = pops.geoid

        pdtracts = pdtracts[pdtracts.isin(tracts)]
        print(pdtracts)


    pops.drop(pops.loc[~pops.geoid.isin(tracts)].index, inplace = True)
    pops.columns = ['geoid', 'demand']


    destTracts = list(data.keys())
    vals = list(data.values())
    vals = np.array(vals)

    docs = pd.DataFrame({'geoid':destTracts, 'supply':vals})
    missingTracts = list(pdtracts[~pdtracts.isin(docs.geoid)])
    missing = pd.DataFrame({'geoid':missingTracts, 'supply':[0]* len(missingTracts)})
    docs = docs.append(missing)
    docs.supply = pd.to_numeric(docs.supply)
    docs.geoid = pd.to_numeric(docs.geoid)
    docs.drop(docs.loc[~docs.geoid.isin(tracts)].index, inplace = True)
    print(docs.head())

    all = []
    travel = pd.DataFrame()

    #Getting list of counties
    counties = []
    for tract in tracts:
        tract = str(tract)
        if len(tract) == 10:
            tract = '0' + tract
        
        counties.append(tract[0:5])
    counties = list(set(counties))

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
    travel.dest = pd.to_numeric(travel.dest)
    validOrigins = list(pops.geoid)
    additionalSelfTimes = pd.DataFrame({'origin': validOrigins, 'dest': validOrigins, 'cost': [0] * len(validOrigins)})
    travel = pd.concat([travel, additionalSelfTimes], ignore_index = True, sort=True)

    if method != 'RAAM':
        docs, pops = FCAPrep(docs, pops)
    else:
        pops, docs = raamPrep(pops, docs)

    
    print(travel.head())
    print(docs.head())
    print(pops.head())
    saveToS3(travel, 'ttime', bucketName)
    saveToS3(docs, 'docs', bucketName, True)
    saveToS3(pops, 'pops', bucketName, True)

    tester = access(demand_df = pops, demand_value = 'demand', 
                    supply_df = docs, supply_value = 'supply',
                    demand_index = True, supply_index = True,
                    cost_df = travel, cost_origin = 'origin', cost_dest = 'dest', cost_name = 'cost',
                    neighbor_cost_df = travel, neighbor_cost_origin = 'dest', 
                    neighbor_cost_dest = 'origin', neighbor_cost_name = 'cost')
    
    if method == 'FCA':
        data = tester.fca_ratio(max_cost = 60)
    elif method == '2SFCA':
        data = tester.two_stage_fca(max_cost = 60)
    #elif method == 'E2SFCA':
    #    data = tester.enhanced_two_stage_fca(max_cost = 60, normalize = True)
    elif method == '3SFCA':
        data = tester.three_stage_fca(max_cost = 60)
    else:
        data = tester.raam()
        data.columns = ['tracts','RAAM']
        data.set_index('tracts', inplace = True)

    
    print(data.head())

    s3Objs = []
    key = 'tempAccessData/' + uuid + '.csv'
    s3.Object(bucketName, key).put(Body = data.to_csv(index = True))
    s3Objs.append('https://' + bucketName + '.s3.us-east-2.amazonaws.com/' + key)
    return {
        'statusCode': 200,
        'body': json.dumps(str(s3Objs))
    }

