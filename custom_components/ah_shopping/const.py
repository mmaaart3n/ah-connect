"""Constants for the AH Shopping integration."""

from __future__ import annotations

from datetime import timedelta
from typing import Final

DOMAIN: Final = "ah_shopping"

# API base
API_BASE: Final = "https://api.ah.nl"
GRAPHQL_PATH: Final = "/graphql"

# Auth (appie-go reference: appie-ios client)
AUTH_ANONYMOUS_TOKEN: Final = f"{API_BASE}/mobile-auth/v1/auth/token/anonymous"
AUTH_TOKEN: Final = f"{API_BASE}/mobile-auth/v1/auth/token"
AUTH_REFRESH: Final = f"{API_BASE}/mobile-auth/v1/auth/token/refresh"

# OAuth – appie-go style login URL; legacy authorize URL kept in docs
OAUTH_LOGIN_URL: Final = (
    "https://login.ah.nl/login"
    "?client_id=appie-ios&response_type=code&redirect_uri=appie://login-exit"
)
OAUTH_AUTHORIZE_URL_LEGACY: Final = (
    "https://login.ah.nl/secure/oauth/authorize"
    "?client_id=appie&redirect_uri=appie://login-exit&response_type=code"
)
CLIENT_ID: Final = "appie-ios"
CLIENT_VERSION: Final = "9.28"
CLIENT_ID_LEGACY: Final = "appie"

# Products
PRODUCT_SEARCH: Final = f"{API_BASE}/mobile-services/product/search/v2"
PRODUCT_SEARCH_BY_IDS: Final = f"{API_BASE}/mobile-services/product/search/v2/products"
PRODUCT_DETAIL: Final = f"{API_BASE}/mobile-services/product/detail/v4/fir"
BONUS_METADATA: Final = f"{API_BASE}/mobile-services/bonuspage/v3/metadata"
BONUS_SECTION: Final = f"{API_BASE}/mobile-services/bonuspage/v2/section"

# Shopping lists
SHOPPING_LISTS_V3: Final = f"{API_BASE}/mobile-services/lists/v3/lists"
SHOPPING_LIST_ITEMS_V2: Final = f"{API_BASE}/mobile-services/shoppinglist/v2/items"
SHOPPING_LIST_ITEM_CHECK: Final = f"{API_BASE}/mobile-services/lists/v3/lists/items"

# Orders (experimental)
ORDER_ACTIVE_SUMMARY: Final = (
    f"{API_BASE}/mobile-services/order/v1/summaries/active?sortBy=DEFAULT"
)
ORDER_ITEMS: Final = f"{API_BASE}/mobile-services/order/v1/items?sortBy=DEFAULT"
ORDER_DETAILS: Final = f"{API_BASE}/mobile-services/order/v1"

# Legacy REST receipts (fallback)
RECEIPTS_LEGACY: Final = f"{API_BASE}/mobile-services/v1/receipts"
RECEIPT_DETAIL_LEGACY: Final = f"{API_BASE}/mobile-services/v2/receipts"

# HTTP headers (appie-go reference)
USER_AGENT: Final = "Appie/9.28 (iPhone17,3; iPhone; CPU OS 26_1 like Mac OS X)"
APPLICATION_HEADER: Final = "AHWEBSHOP"

DEFAULT_TIMEOUT: Final = 30
MIN_REQUEST_INTERVAL: Final = 0.5

# Config entry keys
CONF_ACCESS_TOKEN: Final = "access_token"
CONF_REFRESH_TOKEN: Final = "refresh_token"
CONF_EXPIRES_AT: Final = "expires_at"
CONF_ANONYMOUS: Final = "anonymous"
CONF_AUTH_CODE: Final = "auth_code"
CONF_CLIENT_ID: Final = "client_id"

# Options
CONF_SCAN_INTERVAL: Final = "scan_interval"
CONF_MAX_SEARCH_RESULTS: Final = "max_search_results"
CONF_ENABLE_RECEIPTS: Final = "enable_receipts_sensor"
CONF_ENABLE_REMOTE_SHOPPING_LIST: Final = "enable_remote_shopping_list"
CONF_ENABLE_BONUS_SENSOR: Final = "enable_bonus_sensor"
CONF_EXPERIMENTAL_ORDER: Final = "experimental_order_enabled"
CONF_EXPERIMENTAL_CHECKOUT: Final = "experimental_checkout_enabled"
CONF_EXPERIMENTAL_CART: Final = "experimental_cart_enabled"  # alias legacy

DEFAULT_SCAN_INTERVAL: Final = 3600
DEFAULT_MAX_SEARCH_RESULTS: Final = 10
DEFAULT_ENABLE_RECEIPTS: Final = True
DEFAULT_ENABLE_REMOTE_SHOPPING_LIST: Final = False
DEFAULT_ENABLE_BONUS_SENSOR: Final = False
DEFAULT_EXPERIMENTAL_ORDER: Final = False
DEFAULT_EXPERIMENTAL_CHECKOUT: Final = False

TOKEN_REFRESH_BUFFER: Final = timedelta(minutes=5)

STORAGE_KEY: Final = "ah_shopping_list"
STORAGE_VERSION: Final = 1

EVENT_PRODUCTS_FOUND: Final = "ah_shopping_products_found"
EVENT_RESULT: Final = "ah_shopping_result"

PLATFORMS: Final = ["sensor"]
UPDATE_INTERVAL: Final = timedelta(seconds=DEFAULT_SCAN_INTERVAL)

# GraphQL queries (from appie-go reference, ported to Python strings)
GQL_FETCH_POS_RECEIPTS: Final = """query FetchPosReceipts($offset: Int!, $limit: Int!) {
  posReceiptsPage(pagination: {offset: $offset, limit: $limit}) {
    posReceipts {
      id
      dateTime
      totalAmount { amount }
    }
  }
}"""

GQL_FETCH_RECEIPT: Final = """query FetchReceipt($id: String!) {
  posReceiptDetails(id: $id) {
    id
    products {
      id
      quantity
      name
      price { amount }
      amount { amount }
    }
    discounts { name amount { amount } }
    payments { method amount { amount } }
  }
}"""

GQL_FETCH_MEMBER: Final = """query FetchMember {
  member {
    id
    emailAddress
    name { first last }
    phoneNumber
  }
}"""

GQL_FAVORITE_LIST_V2: Final = """query FavoriteListV2($ids: [String!]!) {
  favoriteListV2(ids: $ids) {
    id
    description
    totalSize
    items { id productId quantity }
  }
}"""

GQL_ORDER_FULFILLMENTS: Final = """query OrderFulfillments {
  orderFulfillments(status: OPEN) {
    result {
      orderId
      statusDescription
      shoppingType
      modifiable
      totalPrice { totalPrice { amount } }
    }
  }
}"""
