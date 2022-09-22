# Credential constants
PHA_USERNAME = ""
PHA_PASSWORD = ""
BOB_AI_USER_ID = ""
BOB_AI_PASSWORD = ""
BOB_AI_API_KEY = ""
PHA_CUSTOMER_CODE = ""
PHA_SOURCE_NAME = "WEB INSPECTION"

#Instance Constants
BOB_INSTANCE = "https://api-staging.bob.ai"

# Other constants
BOB_AI_INSPECTION_GET_URL = "{}/api/inspections/get_list_inspection".format(BOB_INSTANCE)
BOB_AI_PROPOSE_AVAILABLE_SLOT = "{}/api/inspections/propose_slots".format(BOB_INSTANCE)
BOB_AI_CREATE_INSPECTION = "{}/api/inspections/create".format(BOB_INSTANCE)
BOB_AI_CREATE_UNIT = "{}/api/masters/add_unit_address".format(BOB_INSTANCE)
BOB_AI_UPDATE_INSTANCE_ID = "{}/api/inspections/update_inspection_data".format(BOB_INSTANCE)
PHA_INSPECTION_API_URL = "https://www.pha-web.com/inspectionAPI/inspection/activetenants"
BOB_AI_LOGIN_URL = "{}/bobUserApi.xsjs?func=login".format(BOB_INSTANCE)
