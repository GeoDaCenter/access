import json, uuid
import boto3

def lambda_handler(event, context):
    # TODO implement
    uid = 'accessData' + uuid.uuid4().hex
    data = {}
    try:
        data = json.loads(event['body'])
    except:
        data['tract'] = event['tract']
        data['method'] = event['method']
        data['location'] = event['location']
        data['state'] = event['state']
        
    data['id'] = uid
    lambda_client = boto3.client('lambda')
    print("Sending",data)
    byteEvent = json.dumps(data).encode()
    lambda_client.invoke(FunctionName="access",InvocationType='Event', Payload = byteEvent)

    return {
        'statusCode': 200,
        'headers' : {
        'content-type': 'application/json',
        'Access-Control-Allow-Origin': '*' 
    },
        'body': json.dumps('https://tractaccessinfo.s3.us-east-2.amazonaws.com/tempAccessData/' + uid + '.csv')
    }
