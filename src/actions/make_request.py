# File: make_request.py
#
# Copyright (c) 2021-2026 Splunk Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the License for the specific language governing permissions
# and limitations under the License.
import json
from urllib.parse import parse_qsl, unquote, urlsplit

from soar_sdk.action_results import MakeRequestOutput
from soar_sdk.exceptions import ActionFailure
from soar_sdk.params import MakeRequestParams, Param

from ..app import Asset, app
from ..consts import GOOGLE_CONTACTS_SCOPE
from ..helper import create_credentials


PEOPLE_API_BASE_URL = "https://people.googleapis.com"
DEFAULT_REQUEST_TIMEOUT = 30
MAX_REQUEST_TIMEOUT = 300
BLOCKED_HEADERS = {"authorization", "host", "proxy-authorization", "cookie", "content-length", "transfer-encoding"}
ALLOWED_METHODS = {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}


class GooglePeopleMakeRequestParams(MakeRequestParams):
    endpoint: str = Param(
        description=(
            "Relative Google People API v1 endpoint, such as '/v1/people:searchContacts'. "
            "Do not include a URL, query string, or fragment. This request uses the Google Contacts scope."
        ),
        required=True,
    )


def _request_url(endpoint: str) -> str:
    if not isinstance(endpoint, str) or not endpoint.strip():
        raise ActionFailure("The endpoint must be a non-empty Google People API v1 path")
    if any(char.isspace() or ord(char) < 32 or ord(char) == 127 for char in endpoint):
        raise ActionFailure("The endpoint must not contain whitespace or control characters")

    try:
        parsed = urlsplit(endpoint)
    except ValueError as error:
        raise ActionFailure("The endpoint must be a valid relative API path") from error
    path = parsed.path
    decoded_path = unquote(path)
    if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment:
        raise ActionFailure("Provide a relative API path only; use query_parameters for query values")
    if any(char.isspace() or ord(char) < 32 or ord(char) == 127 for char in decoded_path):
        raise ActionFailure("The endpoint must not contain encoded whitespace or control characters")
    if "\\" in decoded_path or any(part in {".", ".."} for part in decoded_path.split("/")):
        raise ActionFailure("The endpoint path contains an invalid path segment")

    normalized_path = path if path.startswith("/") else f"/{path}"
    if not normalized_path.startswith("/v1/") or len(normalized_path) <= len("/v1/"):
        raise ActionFailure("The endpoint must be a Google People API v1 path beginning with '/v1/'")
    return f"{PEOPLE_API_BASE_URL}{normalized_path}"


def _parse_headers(raw_headers: str | None) -> dict[str, str]:
    headers: dict[str, str] = {"Accept": "application/json", "Content-Type": "application/json"}
    if not raw_headers:
        return headers
    try:
        parsed = json.loads(raw_headers)
    except (json.JSONDecodeError, TypeError) as error:
        raise ActionFailure("headers must be a JSON object") from error
    if not isinstance(parsed, dict) or any(not isinstance(key, str) or not isinstance(value, str) for key, value in parsed.items()):
        raise ActionFailure("headers must be a JSON object containing string keys and values")
    blocked = BLOCKED_HEADERS.intersection(key.lower() for key in parsed)
    if blocked:
        raise ActionFailure(f"The following headers are managed by the app and cannot be set: {', '.join(sorted(blocked))}")
    headers.update(parsed)
    return headers


def _parse_query_parameters(raw_parameters: str | None) -> dict | list[tuple[str, str]] | None:
    if not raw_parameters:
        return None
    try:
        parsed = json.loads(raw_parameters)
    except (json.JSONDecodeError, TypeError):
        query = raw_parameters[1:] if raw_parameters.startswith("?") else raw_parameters
        if "#" in query or any(ord(char) < 32 or ord(char) == 127 for char in query):
            raise ActionFailure("query_parameters contains an invalid fragment or control character")
        try:
            pairs = parse_qsl(query, keep_blank_values=True, strict_parsing=True)
        except ValueError as error:
            raise ActionFailure("query_parameters must be a JSON object or a valid query string") from error
        if not pairs:
            raise ActionFailure("query_parameters must contain at least one key/value pair")
        return pairs
    if not isinstance(parsed, dict) or any(not isinstance(key, str) for key in parsed):
        raise ActionFailure("JSON query_parameters must be an object with string keys")
    scalar_types = (str, int, float, bool, type(None))
    if any(
        not isinstance(value, scalar_types) and (not isinstance(value, list) or any(not isinstance(item, scalar_types) for item in value))
        for value in parsed.values()
    ):
        raise ActionFailure("JSON query_parameters values must be strings, numbers, booleans, null, or lists of these values")
    return parsed


@app.make_request()
def make_request(params: GooglePeopleMakeRequestParams, asset: Asset) -> MakeRequestOutput:
    """Send an authenticated request to a relative Google People API v1 endpoint."""
    # Manifest generation runs without app dependencies; keep runtime-only imports local.
    from google.auth.transport.requests import Request as GoogleAuthRequest
    from requests import RequestException, request

    url = _request_url(params.endpoint)
    headers = _parse_headers(params.headers)
    query_parameters = _parse_query_parameters(params.query_parameters)
    timeout = params.timeout if params.timeout is not None else DEFAULT_REQUEST_TIMEOUT
    if timeout <= 0 or timeout > MAX_REQUEST_TIMEOUT:
        raise ActionFailure(f"timeout must be between 1 and {MAX_REQUEST_TIMEOUT} seconds")
    method = params.http_method.upper()
    if method not in ALLOWED_METHODS:
        raise ActionFailure(f"Unsupported HTTP method: {params.http_method}")

    body = None
    json_body = None
    if params.body:
        content_type = next((value for key, value in headers.items() if key.lower() == "content-type"), "")
        if "json" in content_type.lower():
            try:
                json_body = json.loads(params.body)
            except (json.JSONDecodeError, TypeError) as error:
                raise ActionFailure("body must contain valid JSON when Content-Type is JSON") from error
        else:
            body = params.body

    credentials = create_credentials(asset, [GOOGLE_CONTACTS_SCOPE])
    try:
        credentials.refresh(GoogleAuthRequest(timeout=timeout))
    except Exception as error:
        raise ActionFailure("Failed to obtain an access token for the Google People API") from error

    headers["Authorization"] = f"Bearer {credentials.token}"
    try:
        response = request(
            method=method,
            url=url,
            headers=headers,
            params=query_parameters,
            data=body,
            json=json_body,
            timeout=timeout,
            verify=params.verify_ssl if params.verify_ssl is not None else True,
        )
    except RequestException as error:
        raise ActionFailure(f"Google People API request failed: {error}") from error

    # Keep non-2xx responses as action output, matching the SDK make_request contract.
    return MakeRequestOutput(status_code=response.status_code, response_body=response.text)
