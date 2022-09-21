import requests
import json
import logging
import base64
import sys

from phaweb_configs import *

logging.basicConfig(filename="pha_update_date_back.log",
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
    elif r.headers.get('Content-Length', '0') == '0':
        if (200 <= r.status_code < 205):
            return True, ''
        
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

def get_integration_data():

    headers = {
        'Authorization': 'Bearer {}'.format(BOB_AI_API_KEY)
    }

    ret_val, response = _make_rest_call(url="http://api-staging.bob.ai/api/data_logs/get_integration_data?type=export&action=update_unit&status=PENDING", headers=headers, method="get")

    return ret_val, response

def update_integration_data(unit_id):

    headers = {
        'Authorization': 'Bearer {}'.format(BOB_AI_API_KEY)
    }

    payload = {
        "id": unit_id,
        "status": "COMPLETED"
    }

    ret_val, response = _make_rest_call(url="http://api-staging.bob.ai/api/data_logs/update_integration_data", data=json.dumps(payload), headers=headers, method="post")

    return ret_val, response

def update_date_to_pha(tenantid, unitid, lastannualdate, lastpasseddate):

    auth_header = base64.b64encode('{}:{}'.format(PHA_USERNAME, PHA_PASSWORD).encode()).decode()

    headers = {
        'Authorization': 'Basic {}'.format(auth_header),
        'Content-Type': 'application/json'
    }

    params = {
        "tenantid": tenantid,
        "unitid": unitid
    }

    if lastannualdate and lastpasseddate:
        payload = {
            "LastAnnualInspectionDate": lastannualdate,
            "LastPassedInspectionDate": lastpasseddate
        }
    elif lastannualdate:
        payload = {
            "LastAnnualInspectionDate": lastannualdate
        }
    elif lastpasseddate:
        payload = {
            "LastPassedInspectionDate": lastpasseddate
        }

    ret_val, response = _make_rest_call(url="https://www.pha-web.com/inspectionAPI/inspection/activetenants", data=json.dumps(payload), params=params, headers=headers, method="put")

    return ret_val, response


ret_val, integration_data_response = get_integration_data()
if not ret_val:
    logger.debug("Error while updating inspection date back to PHA. Error {}".format(integration_data_response))
    sys.exit()

integration_data = integration_data_response.get("data", [])

if not integration_data:
    logger.debug("No integration data found")
    sys.exit()

for data in integration_data:
    tenant_id = data.get("data", {}).get("tenant_id")
    unit_id = data.get("id")
    last_scheduled_date = data.get("data", {}).get("last_scheduled_date")
    last_passed_date = data.get("data", {}).get("last_passed_date")

    # tenant_id = 954257
    # unit_id = 310149
    # last_scheduled_date = "2022-09-20 12:00:00"
    # last_passed_date = "2022-09-20 12:00:00"


    if not all([tenant_id, unit_id]):
        logger.debug("unit id and tenant id both must be provided. Error for data {}".format(data))
        continue

    if not last_scheduled_date and not last_passed_date:
        logger.debug("Either last scheduled date or last passed date must be provided. Error for data {}".format(data))
        continue

    ret_val, update_pha_response = update_date_to_pha(tenant_id, unit_id, last_scheduled_date, last_passed_date)
    if not ret_val:
        logger.debug("Error while updating inspection date back to PHA for data {}. Error {}".format(data, update_pha_response))
        continue
    
    ret_val, integration_update_response = update_integration_data(unit_id)
    if not ret_val:
        logger.debug("Error while updating integration status back to BOB for data {}. Error {}".format(data, integration_update_response))
        continue

logger.debug("Script executed successfully")