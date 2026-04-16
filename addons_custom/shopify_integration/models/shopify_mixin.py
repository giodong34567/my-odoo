"""ShopifyAPIMixin — the ONLY place that reads access_token and makes HTTP calls."""
import re
import time
import logging
import requests
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)
_DEFAULT_RETRY_SLEEP = 2
_API_VERSION = '2026-04'


class ShopifyAPIMixin:
    """Mix into any service class that needs to call the Shopify REST API.

    Usage:
        class ProductSync(ShopifyAPIMixin):
            def __init__(self, config):
                super().__init__(config)
    """

    def __init__(self, config):
        self._config = config
        self._env = config.env

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def call(self, method, path, params=None, payload=None):
        """Make a single authenticated Shopify API call.

        Handles 429 rate-limiting with Retry-After back-off (default 2 s).
        Raises UserError on any other HTTP error.
        Returns parsed JSON dict/list.
        """
        url = self._url(path)
        response = self._do_request(method, url, params=params, json=payload)

        if response.status_code == 429:
            sleep_for = float(response.headers.get('Retry-After', _DEFAULT_RETRY_SLEEP))
            _logger.warning('Shopify rate limit — sleeping %s s then retrying.', sleep_for)
            time.sleep(sleep_for)
            response = self._do_request(method, url, params=params, json=payload)

        self._raise_for_status(response)
        return response.json()

    def paginate(self, path, params=None):
        """Fetch all pages from a paginated Shopify endpoint.

        Follows the Link header (rel="next") until exhausted.
        Returns a flat list of all items across all pages.
        """
        params = dict(params or {})
        params.setdefault('limit', 250)
        url = self._url(path)
        all_items = []

        while url:
            response = self._do_request('GET', url, params=params)

            if response.status_code == 429:
                sleep_for = float(response.headers.get('Retry-After', _DEFAULT_RETRY_SLEEP))
                _logger.warning('Shopify rate limit during pagination — sleeping %s s.', sleep_for)
                time.sleep(sleep_for)
                continue  # retry same url

            self._raise_for_status(response)

            data = response.json()
            for value in data.values():
                if isinstance(value, list):
                    all_items.extend(value)
                    break

            url = self._next_link(response.headers.get('Link', ''))
            params = {}  # next URL already contains query params

        return all_items

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _url(self, path):
        base = self._config.shop_url.rstrip('/')
        return f'{base}/admin/api/{_API_VERSION}{path}'

    def _headers(self):
        # access_token is read ONLY here — never passed to logs or exceptions
        return {
            'X-Shopify-Access-Token': self._config.access_token,
            'Content-Type': 'application/json',
        }

    def _do_request(self, method, url, **kwargs):
        kwargs.setdefault('headers', self._headers())
        kwargs.setdefault('timeout', 30)
        return requests.request(method, url, **kwargs)

    @staticmethod
    def _raise_for_status(response):
        if not response.ok:
            raise UserError(
                f'Shopify API error {response.status_code}: {response.text[:500]}'
            )

    @staticmethod
    def _next_link(link_header):
        for part in link_header.split(','):
            if 'rel="next"' in part:
                m = re.search(r'<([^>]+)>', part)
                if m:
                    return m.group(1)
        return None
