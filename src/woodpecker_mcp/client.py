from __future__ import annotations

import asyncio
import logging
import random
from contextvars import ContextVar, Token
from types import TracebackType
from typing import Any

import httpx

from . import __version__ as _version
from .errors import WoodpeckerError

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT = httpx.Timeout(connect=5.0, read=30.0, write=30.0, pool=5.0)
_DEFAULT_PER_PAGE = 50
_MAX_PER_PAGE = 100
_DEFAULT_MAX_RETRIES = 3
_DEFAULT_BACKOFF_BASE = 1.0
_DEFAULT_BACKOFF_MAX = 10.0
_RETRYABLE_STATUS_CODES = {500, 502, 503, 504, 429}


class WoodpeckerClient:
    """Async HTTP client for Woodpecker API with automatic retry logic.

    Automatically retries transient failures (network errors, 5xx, 429) with
    exponential backoff. GET and DELETE requests retry by default; POST requests
    only retry if explicitly enabled.
    """

    def __init__(
        self,
        base_url: str,
        token: str,
        *,
        timeout: httpx.Timeout = _DEFAULT_TIMEOUT,
        transport: httpx.AsyncBaseTransport | None = None,
        max_retries: int = _DEFAULT_MAX_RETRIES,
        retry_backoff_base: float = _DEFAULT_BACKOFF_BASE,
        retry_backoff_max: float = _DEFAULT_BACKOFF_MAX,
    ) -> None:
        """Initialize Woodpecker client.

        Args:
            base_url: Woodpecker server URL (e.g. 'https://ci.example.com')
            token: API authentication token
            timeout: HTTP timeout configuration
            transport: Optional custom HTTP transport (for testing)
            max_retries: Maximum number of retry attempts (default: 3)
            retry_backoff_base: Base delay in seconds for exponential backoff (default: 1.0)
            retry_backoff_max: Maximum delay in seconds (default: 10.0)
        """
        self._base_url = base_url.rstrip("/")
        self._max_retries = max_retries
        self._retry_backoff_base = retry_backoff_base
        self._retry_backoff_max = retry_backoff_max
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=timeout,
            follow_redirects=False,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
                "User-Agent": f"woodpecker-mcp/{_version}",
            },
            transport=transport,
        )

    @property
    def base_url(self) -> str:
        return self._base_url

    def _url(self, path: str) -> str:
        return f"/api{path}"

    async def __aenter__(self) -> WoodpeckerClient:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._client.aclose()

    async def _request_with_retry(
        self,
        method: str,
        path: str,
        *,
        retry: bool | None = None,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> httpx.Response:
        """Execute HTTP request with automatic retry for transient failures.

        Retries on network errors (ConnectError, TimeoutException) and HTTP 5xx/429
        responses using exponential backoff with jitter. Respects Retry-After header
        when present.

        Args:
            method: HTTP method (GET, POST, DELETE, etc.)
            path: API path (without /api prefix)
            retry: Override default retry behavior. None = use default
                   (True for GET/DELETE, False for POST/PUT/PATCH)
            json: JSON body for request
            params: Query parameters

        Returns:
            httpx.Response object

        Raises:
            WoodpeckerError: For non-retryable HTTP errors
            httpx.ConnectError: For network failures after all retries exhausted
            httpx.TimeoutException: For timeouts after all retries exhausted
        """
        should_retry = method.upper() in ("GET", "DELETE") if retry is None else retry

        url = self._url(path)
        last_exception: Exception | None = None
        resp: httpx.Response | None = None

        for attempt in range(self._max_retries + 1):
            try:
                resp = await self._client.request(
                    method,
                    url,
                    json=json,
                    params=_clean_params(params),
                )

                if resp.status_code in _RETRYABLE_STATUS_CODES and should_retry:
                    if attempt < self._max_retries:
                        retry_after = resp.headers.get("Retry-After")
                        delay = self._calculate_delay(attempt, retry_after)
                        logger.warning(
                            "Request to %s %s failed with %d, retrying in %.2fs (attempt %d/%d)",
                            method,
                            path,
                            resp.status_code,
                            delay,
                            attempt + 1,
                            self._max_retries,
                        )
                        await asyncio.sleep(delay)
                        continue
                    else:
                        return resp
                else:
                    return resp

            except (httpx.ConnectError, httpx.TimeoutException) as e:
                last_exception = e
                if should_retry and attempt < self._max_retries:
                    delay = self._calculate_delay(attempt)
                    logger.warning(
                        "Request to %s %s failed with %s, retrying in %.2fs (attempt %d/%d)",
                        method,
                        path,
                        type(e).__name__,
                        delay,
                        attempt + 1,
                        self._max_retries,
                    )
                    await asyncio.sleep(delay)
                    continue
                else:
                    raise

        if last_exception:
            raise last_exception
        if resp:
            return resp
        raise RuntimeError("Unexpected state in _request_with_retry")

    def _calculate_delay(self, attempt: int, retry_after: str | None = None) -> float:
        """Calculate delay with exponential backoff and jitter.

        Args:
            attempt: Current attempt number (0-indexed)
            retry_after: Optional Retry-After header value in seconds

        Returns:
            Delay in seconds
        """
        if retry_after:
            try:
                return float(retry_after)
            except ValueError:
                pass

        delay = self._retry_backoff_base * (2**attempt)
        delay += random.random()
        return min(delay, self._retry_backoff_max)

    async def get_json(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        retry: bool | None = None,
    ) -> Any:
        """Execute GET request and return JSON response.

        Automatically retries on transient failures by default.

        Args:
            path: API path (without /api prefix)
            params: Query parameters
            retry: Override default retry behavior (default: True for GET)

        Returns:
            Parsed JSON response
        """
        return await self._json("GET", path, params=params, retry=retry)

    async def post_json(
        self,
        path: str,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        retry: bool | None = None,
    ) -> Any:
        """Execute POST request and return JSON response.

        Does NOT retry by default (POST may not be idempotent).
        Set retry=True to enable retries for idempotent POST operations.

        Args:
            path: API path (without /api prefix)
            json: JSON body for request
            params: Query parameters
            retry: Override default retry behavior (default: False for POST)

        Returns:
            Parsed JSON response
        """
        return await self._json("POST", path, json=json, params=params, retry=retry)

    async def delete(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        retry: bool | None = None,
    ) -> None:
        """Execute DELETE request.

        Automatically retries on transient failures by default.

        Args:
            path: API path (without /api prefix)
            params: Query parameters
            retry: Override default retry behavior (default: True for DELETE)
        """
        resp = await self._request_with_retry(
            "DELETE",
            path,
            retry=retry,
            params=params,
        )
        _raise_for_status(resp)

    async def paginate(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        page: int = 1,
        per_page: int = _DEFAULT_PER_PAGE,
    ) -> dict[str, Any]:
        merged = dict(params or {})
        merged["page"] = page
        merged["perPage"] = min(per_page, _MAX_PER_PAGE)
        data = await self.get_json(path, params=merged)
        if isinstance(data, list):
            return {
                "items": data,
                "page": page,
                "per_page": merged["perPage"],
            }
        return {
            "items": data,
            "page": page,
            "per_page": merged["perPage"],
        }

    async def _json(
        self,
        method: str,
        path: str,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        retry: bool | None = None,
    ) -> Any:
        resp = await self._request_with_retry(
            method,
            path,
            retry=retry,
            json=json,
            params=params,
        )
        _raise_for_status(resp)
        if not resp.content:
            return None
        return resp.json()


def _clean_params(params: dict[str, Any] | None) -> dict[str, Any] | None:
    if not params:
        return None
    return {k: v for k, v in params.items() if v is not None}


def _raise_for_status(resp: httpx.Response) -> None:
    if resp.is_success:
        return
    status = resp.status_code
    body: Any = None
    errors: list[str] = []
    message = resp.reason_phrase or "request failed"
    try:
        body = resp.json()
    except ValueError:
        body = resp.text or None
    if isinstance(body, dict):
        raw = body.get("errors")
        if isinstance(raw, list):
            errors = [str(e) for e in raw]
            if errors and not message:
                message = errors[0]
        raw_msg = body.get("message")
        if raw_msg:
            message = str(raw_msg)
    if status == 401:
        message = "invalid Woodpecker API token or unauthorized"
    elif status == 403:
        message = errors[0] if errors else "forbidden"
    elif status == 404:
        message = "not found"
    raise WoodpeckerError(status, message, errors=errors, body=body)


_current_client: ContextVar[WoodpeckerClient | None] = ContextVar("woodpecker_client", default=None)


def set_current_client(client: WoodpeckerClient | None) -> Token[WoodpeckerClient | None]:
    return _current_client.set(client)


def reset_current_client(token: Token[WoodpeckerClient | None]) -> None:
    _current_client.reset(token)


def get_woodpecker_client() -> WoodpeckerClient:
    client = _current_client.get()
    if client is None:
        raise RuntimeError(
            "no WoodpeckerClient bound to this request; Authorization header must be set"
        )
    return client
