"""Constants for the AH Shopping integration."""

from __future__ import annotations

from datetime import timedelta
from typing import Final

DOMAIN: Final = "ah_shopping"

# API endpoints
API_BASE: Final = "https://api.ah.nl"
AUTH_ANONYMOUS_TOKEN: Final = f"{API_BASE}/mobile-auth/v1/auth/token/anonymous"
AUTH_TOKEN: Final = f"{API_BASE}/mobile-auth/v1/auth/token"
AUTH_REFRESH: Final = f"{API_BASE}/mobile-auth/v1/auth/token/refresh"
PRODUCT_SEARCH: Final = f"{API_BASE}/mobile-services/product/search/v2"
RECEIPTS: Final = f"{API_BASE}/mobile-services/v1/receipts"
RECEIPT_DETAIL: Final = f"{API_BASE}/mobile-services/v2/receipts"

# OAuth
OAUTH_AUTHORIZE_URL: Final = (
    "https://login.ah.nl/secure/oauth/authorize"
    "?client_id=appie&redirect_uri=appie://login-exit&response_type=code"
)
CLIENT_ID: Final = "appie"

# HTTP
USER_AGENT: Final = "Appie/8.22.3"
DEFAULT_TIMEOUT: Final = 30
MIN_REQUEST_INTERVAL: Final = 0.5  # seconds between API calls

# Config entry keys
CONF_ACCESS_TOKEN: Final = "access_token"
CONF_REFRESH_TOKEN: Final = "refresh_token"
CONF_EXPIRES_AT: Final = "expires_at"
CONF_ANONYMOUS: Final = "anonymous"
CONF_AUTH_CODE: Final = "auth_code"

# Options
CONF_SCAN_INTERVAL: Final = "scan_interval"
CONF_MAX_SEARCH_RESULTS: Final = "max_search_results"
CONF_ENABLE_RECEIPTS: Final = "enable_receipts_sensor"
CONF_EXPERIMENTAL_CART: Final = "experimental_cart_enabled"

DEFAULT_SCAN_INTERVAL: Final = 3600  # seconds
DEFAULT_MAX_SEARCH_RESULTS: Final = 10
DEFAULT_ENABLE_RECEIPTS: Final = True
DEFAULT_EXPERIMENTAL_CART: Final = False

# Token refresh buffer – refresh 5 minutes before expiry
TOKEN_REFRESH_BUFFER: Final = timedelta(minutes=5)

# Storage
STORAGE_KEY: Final = "ah_shopping_list"
STORAGE_VERSION: Final = 1

# Events
EVENT_PRODUCTS_FOUND: Final = "ah_shopping_products_found"

# Platforms
PLATFORMS: Final = ["sensor"]

# Coordinator
UPDATE_INTERVAL: Final = timedelta(seconds=DEFAULT_SCAN_INTERVAL)
