import unirest
import json
#from flask import json
access_token = 'sq0atp-C2DFF2ap0WWupWFr3A595g'

response = unirest.get('https://connect.squareup.com/v2/locations', headers= {
  'Accept': 'application/json',
  'Authorization': 'Bearer ' + access_token
})

result = response.body['locations']
location_id = result[0]['id']
