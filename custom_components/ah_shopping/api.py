"""AH API client for the AH Shopping integration."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .auth import AhAuthManager
from .const import (
    DEFAULT_TIMEOUT,
    MIN_REQUEST_INTERVAL,
    PRODUCT_SEARCH,
    RECEIPT_DETAIL,
    RECEIPTS,
    USER_AGENT,
)
from .exceptions import AhApiError, AhAuthError, AhRateLimitError, AhUnavailableError
from .models import AhProduct, AhReceipt

_LOGGER = logging.getLogger(__name__)


class AhApiClient:
    """Async client for the Albert Heijn mobile API."""

    def __init__(self, hass: HomeAssistant, auth: AhAuthManager) -> None:
        """Initialize the API client."""
        self._hass = hass
        self._auth = auth
        self._session = async_get_clientsession(hass)
        self._lock = asyncio.Lock()
        self._last_request: float = 0.0

    async def _throttle(self) -> None:
        """Enforce minimum interval between API calls."""
        async with self._lock:
            elapsed = time.monotonic() - self._last_request
            if elapsed < MIN_REQUEST_INTERVAL:
                await asyncio.sleep(MIN_REQUEST_INTERVAL - elapsed)
            self._last_request = time.monotonic()

    async def _request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        require_auth: bool = True,
    ) -> Any:
        """Make an authenticated API request with retry/backoff."""
        max_retries = 3
        backoff = 1.0

        for attempt in range(max_retries):
            await self._throttle()
            headers = {
                "User-Agent": USER_AGENT,
                "Content-Type": "application/json",
            }
            if require_auth:
                try:
                    token = await self._auth.get_access_token()
                    headers["Authorization"] = f"Bearer {token}"
                except AhAuthError:
                    raise

            timeout = aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT)
            try:
                async with self._session.request(
                    method,
                    url,
                    params=params,
                    headers=headers,
                    timeout=timeout,
                ) as response:
                    if response.status == 429:
                        if attempt < max_retries - 1:
                            _LOGGER.warning(
                                "Rate limited by AH API, retrying in %.1fs",
                                backoff,
                            )
                            await asyncio.sleep(backoff)
                            backoff *= 2
                            continue
                        raise AhRateLimitError("Rate limit exceeded")

                    if response.status >= 500:
                        if attempt < max_retries - 1:
                            _LOGGER.warning(
                                "AH API unavailable (HTTP %s), retrying in %.1fs",
                                response.status,
                                backoff,
                            )
                            await asyncio.sleep(backoff)
                            backoff *= 2
                            continue
                        raise AhUnavailableError(
                            f"AH API unavailable (HTTP {response.status})"
                        )

                    if response.status == 401:
                        raise AhAuthError(
                            "Unauthorized. Token may be expired – re-authenticate."
                        )

                    if response.status >= 400:
                        raise AhApiError(
                            f"AH API error (HTTP {response.status})"
                        )

                    return await response.json(content_type=None)

            except aiohttp.ClientError as err:
                if attempt < max_retries - 1:
                    _LOGGER.warning(
                        "Network error contacting AH API, retrying in %.1fs: %s",
                        backoff,
                        type(err).__name__,
                    )
                    await asyncio.sleep(backoff)
                    backoff *= 2
                    continue
                raise AhUnavailableError(
                    f"Network error contacting AH API: {type(err).__name__}"
                ) from err

        raise AhUnavailableError("Max retries exceeded")

    async def search_products(
        self, query: str, *, limit: int = 10
    ) -> list[AhProduct]:
        """Search for products by query string."""
        _LOGGER.debug("Searching products: query=%s, limit=%d", query, limit)
        data = await self._request(
            "GET",
            PRODUCT_SEARCH,
            params={"query": query, "sortOn": "RELEVANCE", "size": limit},
        )

        products: list[AhProduct] = []
        items = self._extract_product_list(data)
        for item in items[:limit]:
            try:
                products.append(AhProduct.from_api(item))
            except (KeyError, TypeError, ValueError) as err:
                _LOGGER.debug("Skipping malformed product entry: %s", type(err).__name__)

        return products

    def _extract_product_list(self, data: Any) -> list[dict[str, Any]]:
        """Extract product list from various response shapes."""
        if isinstance(data, list):
            return [i for i in data if isinstance(i, dict)]
        if not isinstance(data, dict):
            return []

        for key in ("products", "items", "results", "data"):
            items = data.get(key)
            if isinstance(items, list):
                return [i for i in items if isinstance(i, dict)]

        # Nested search result
        search_result = data.get("searchResult") or data.get("productSearch")
        if isinstance(search_result, dict):
            for key in ("products", "items"):
                items = search_result.get(key)
                if isinstance(items, list):
                    return [i for i in items if isinstance(i, dict)]

        return []

    async def get_receipts(self) -> list[AhReceipt]:
        """Fetch receipt summaries (authenticated only)."""
        if self._auth.is_anonymous:
            raise AhAuthError("Receipts require authenticated mode")

        _LOGGER.debug("Fetching receipts")
        data = await self._request("GET", RECEIPTS)

        receipts: list[AhReceipt] = []
        items = self._extract_receipt_list(data)
        for item in items:
            try:
                receipts.append(AhReceipt.from_api(item))
            except (KeyError, TypeError, ValueError) as err:
                _LOGGER.debug("Skipping malformed receipt: %s", type(err).__name__)

        return receipts

    def _extract_receipt_list(self, data: Any) -> list[dict[str, Any]]:
        """Extract receipt list from various response shapes."""
        if isinstance(data, list):
            return [i for i in data if isinstance(i, dict)]
        if not isinstance(data, dict):
            return []

        for key in ("receipts", "items", "data", "results"):
            items = data.get(key)
            if isinstance(items, list):
                return [i for i in items if isinstance(i, dict)]
        return []

    async def get_receipt_detail(self, transaction_id: str) -> AhReceipt:
        """Fetch detailed receipt by transaction ID."""
        if self._auth.is_anonymous:
            raise AhAuthError("Receipt detail requires authenticated mode")

        url = f"{RECEIPT_DETAIL}/{transaction_id}"
        data = await self._request("GET", url)
        if isinstance(data, dict):
            return AhReceipt.from_api(data)
        raise AhApiError("Unexpected receipt detail response format")
