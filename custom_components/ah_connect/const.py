"""Constants for AH Connect (aligned with appie-go)."""

from __future__ import annotations

DOMAIN = "ah_connect"
NAME = "AH Connect"

DEFAULT_BASE_URL = "https://api.ah.nl"
DEFAULT_USER_AGENT = "Appie/9.28 (iPhone17,3; iPhone; CPU OS 26_1 like Mac OS X)"
DEFAULT_CLIENT_ID = "appie-ios"
DEFAULT_CLIENT_VERSION = "9.28"

CONF_ANONYMOUS = "anonymous"
CONF_CLIENT_ID = "client_id"
CONF_ACCESS_TOKEN = "access_token"
CONF_REFRESH_TOKEN = "refresh_token"
CONF_EXPIRES_AT = "expires_at"
CONF_MEMBER_ID = "member_id"
CONF_AUTH_METHOD = "auth_method"
CONF_APPIE_CONFIG_JSON = "appie_config_json"
CONF_AUTHORIZATION_CODE = "authorization_code"

AUTH_METHOD_ANONYMOUS = "anonymous"
AUTH_METHOD_APPIE_CONFIG = "appie_config"
AUTH_METHOD_AUTHORIZATION_CODE = "authorization_code"

FLOW_MODE_ANONYMOUS = "anonymous"
FLOW_MODE_AUTHENTICATED_APPIE_CONFIG = "authenticated_appie_config"
FLOW_MODE_ADVANCED_AUTHORIZATION_CODE = "advanced_authorization_code"

# Options
OPT_SCAN_INTERVAL = "scan_interval"
OPT_MAX_SEARCH_RESULTS = "max_search_results"
OPT_ENABLE_RECEIPTS_SENSOR = "enable_receipts_sensor"
OPT_ENABLE_REMOTE_SHOPPING_LIST = "enable_remote_shopping_list"
OPT_ENABLE_BONUS_SENSOR = "enable_bonus_sensor"
OPT_EXPERIMENTAL_ORDER_ENABLED = "experimental_order_enabled"
OPT_EXPERIMENTAL_CHECKOUT_ENABLED = "experimental_checkout_enabled"
OPT_DEBUG_LOGGING = "debug_logging"

DEFAULT_SCAN_INTERVAL = 300
DEFAULT_MAX_SEARCH_RESULTS = 10

# Auth paths (appie-go)
PATH_AUTH_ANONYMOUS = "/mobile-auth/v1/auth/token/anonymous"
PATH_AUTH_TOKEN = "/mobile-auth/v1/auth/token"
PATH_AUTH_REFRESH = "/mobile-auth/v1/auth/token/refresh"
LOGIN_URL_TEMPLATE = (
    "https://login.ah.nl/login?client_id={client_id}"
    "&response_type=code&redirect_uri=appie://login-exit"
)

# Events
EVENT_RESULT = "ah_connect_result"

# Coordinator keys
COORD_LAST_RECEIPT = "last_receipt"
COORD_SHOPPING_LIST_COUNT = "shopping_list_count"
COORD_BONUS_COUNT = "bonus_count"
COORD_ORDER_SUMMARY = "order_summary"
