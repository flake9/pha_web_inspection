import requests
import json
import logging
import base64
import sys
from datetime import datetime

from phaweb_configs import *

logging.basicConfig(filename="one_time_script.log",
                    format='%(asctime)s %(message)s',
                    filemode='w')

# Creating an object
logger = logging.getLogger()
 
# Setting the threshold of logger to DEBUG
logger.setLevel(logging.DEBUG)

def _make_rest_call(url=None, params=None, headers=None, data=None, method="get"):
    ''' 
    function to make rest call
    '''

    try:
        request_func = getattr(requests, method)
    except Exception as e:
        error_message = str(e)
        return False, error_message

    try:
        response = request_func(url, params=params, headers=headers, data=data)
    except Exception as e:
        error_message = str(e)
        return False, error_message

    return _process_response(response)

def _process_response(r):
    ''' 
    function to process response
    '''

    # Process a json response
    if 'json' in r.headers.get('Content-Type', ''):
        return _process_json_response(r)

    message = "Can't process response from server. Status Code: {0} Data from server: {1}".format(
            r.status_code, r.text.replace('{', '{{').replace('}', '}}'))

    return False, message

def _process_json_response(r):
    ''' 
    function to process json response
    '''

    # Try a json parse
    try:
        resp_json = r.json()
    except Exception as e:
        logger.debug('Cannot parse JSON')
        return False, "Unable to parse response as JSON"

    if (200 <= r.status_code < 205):
        return True, resp_json

    error_info = resp_json if type(resp_json) is str else resp_json.get('error', {})
    try:
        if error_info.get('code') and error_info.get('message') and type(resp_json):
            error_details = {
                'message': error_info.get('code'),
                'detail': error_info.get('message')
            }
            return False, "Error from server, Status Code: {0} data returned: {1}".format(r.status_code, error_details)
        else:
            return False, "Error from server, Status Code: {0} data returned: {1}".format(r.status_code, r.text.replace('{', '{{').replace('}', '}}'))
    except:
        return False, "Error from server, Status Code: {0} data returned: {1}".format(r.status_code, r.text.replace('{', '{{').replace('}', '}}'))


def _create_master_data(payload):
    ''' 
    function to create master data
    '''

    headers = {
        'Authorization': 'Bearer {}'.format(BOB_AI_API_KEY)
    }

    ret_val, response = _make_rest_call(url="http://api-staging.bob.ai/api/masters/create_new_data", data=payload, headers=headers, method="post")

    return ret_val, response



""" Main Block """

auth_header = base64.b64encode('{}:{}'.format(PHA_USERNAME, PHA_PASSWORD).encode()).decode()

inspection_headers = {
    'Authorization': 'Basic {}'.format(auth_header)
}

ret_val, pha_response = _make_rest_call(url=PHA_INSPECTION_API_URL, headers=inspection_headers, method="get")
if not ret_val:
    logger.debug("Error while fetching units, landlord and tenant details from PHA WEB. Exiting. Error {}".format(pha_response))
    sys.exit()

if not pha_response:
    logger.debug("No data found on PHA WEB. Exiting.")
    sys.exit()

for inspection in pha_response:

    last_passed_date = inspection.get('LastPassedInspectionDate', "")
    last_scheduled_date = inspection.get('LastAnnualInspectionDate', "")

    if last_passed_date:
        last_passed_date = datetime.strptime(last_passed_date, '%m/%d/%Y %H:%M:%S %p').strftime('%Y-%m-%d')
    
    if last_scheduled_date:
        last_scheduled_date = datetime.strptime(last_scheduled_date, '%m/%d/%Y %H:%M:%S %p').strftime('%Y-%m-%d')

    payload = {
        "count": 1,
        "customer_code": "TX009",
        "source_name": "WEB INSPECTION",
        "data": [
            {
                "client": {
                    "id": None,
                    "external_id": str(inspection.get("TenantID","")),
                    "first_name": inspection.get("TenantFirstName" ,""),
                    "last_name": inspection.get("TenantLastName",""),
                    "email": inspection.get("TenantEmail",""),
                    "phone_number": inspection.get("TenantPrimaryPhone",""),
                    "home_number": ""
                },
                "landlord": {
                    "id": None,
                    "external_id": str(inspection.get("LandlordID","")),
                    "name": inspection.get("LandlordName",""),
                    "first_name": "",
                    "last_name": "",
                    "email": inspection.get("LandlordEmail",""),
                    "phone_number": inspection.get("LandlordPrimaryPhone",""),
                    "office_number": ""
                },
                "unit": {
                    "id": None,
                    "external_id": str(inspection.get("UnitID","")),
                    "address1": inspection.get("UnitAddressUnit",""),
                    "address2": inspection.get("UnitAddressLine1",""),
                    "address3": inspection.get("UnitAddressLine2",""),
                    "city": inspection.get("UnitAddressCity",""),
                    "state": inspection.get("UnitAddressState",""),
                    "zipcode": inspection.get("UnitAddressZip",""),
                    "bedroom": inspection.get("UnitBedrooms",""),
                    "last_scheduled_date": str(last_scheduled_date),
                    "last_passed_date": str(last_passed_date)
                }
            }
        ]
    }

    ret_val, master_response = _create_master_data(json.dumps(payload))
    
    if not ret_val:
        error_data = {
            "client_id": inspection.get("TenantID",""),
            "landloard_id": inspection.get("LandlordID",""),
            "unit_id": inspection.get("UnitID","")
        }
        logger.debug("Error while creating master data for tenant {}. Error {}".format(error_data, master_response))
    
    logger.debug(ret_val)
    logger.debug(master_response)

logger.debug("Script executed successfully")