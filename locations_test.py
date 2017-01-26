import unirest
import json
#from flask import json
access_token = 'sandbox-sq0atb-AuykGFFuHYzEFDweaQpdyA'

response = unirest.get('https://connect.squareup.com/v2/locations', headers= {
  'Accept': 'application/json',
  'Authorization': 'Bearer ' + access_token
})

result = response.body['locations']
# this location id allows credit card processing
location_id = result[1]['id']
print result[1]['id']
