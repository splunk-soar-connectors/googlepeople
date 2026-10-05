# File: helper.py
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

from soar_sdk.exceptions import ActionFailure
from soar_sdk.shims.phantom.utils import is_email

from .consts import (
    ERROR_CODE_MESSAGE,
    ERROR_MESSAGE_UNAVAILABLE,
    INVALID_COMMA_SEPARATED_ERROR_MESSAGE,
    INVALID_INTEGER_ERROR_MESSAGE,
    INVALID_NON_ZERO_NON_NEGATIVE_INTEGER_ERROR_MESSAGE,
    LIMIT_KEY,
    PARSE_ERROR_MESSAGE,
)


def error_message(error):
    """Keep the legacy exception formatter's user-visible messages."""
    error_code = ERROR_CODE_MESSAGE
    message = ERROR_MESSAGE_UNAVAILABLE
    if error.args:
        if len(error.args) > 1:
            error_code, message = error.args[:2]
        else:
            message = error.args[0]
    try:
        if error_code in ERROR_CODE_MESSAGE:
            return f"Error Message: {message}"
        return f"Error Code: {error_code}. Error Message: {message}"
    except (TypeError, ValueError):
        return PARSE_ERROR_MESSAGE


def create_client(asset, scopes):
    # Manifest generation imports this module in the soarapps tool environment,
    # which may lack app dependencies. Google imports must stay runtime-only.
    from google.oauth2 import service_account
    from googleapiclient import discovery

    try:
        key_dict = json.loads(asset.key_json)
    except (TypeError, ValueError) as error:
        raise ActionFailure(
            "Please provide a valid value for the 'Contents of service account JSON file' asset configuration parameter"
        ) from error
    if not is_email(asset.login_email):
        raise ActionFailure("Please provide a valid value for the 'Login email' asset configuration parameter")
    try:
        # Google service-account JWT delegation is not a client-credentials flow.
        # Keep Google's credential refresh and per-action scopes as in the legacy app.
        credentials = service_account.Credentials.from_service_account_info(key_dict, scopes=scopes)
    except Exception as error:
        raise ActionFailure(f"Unable to get the credentials from the key json. {error_message(error)}") from error
    try:
        credentials = credentials.with_subject(asset.login_email)
    except Exception as error:
        raise ActionFailure(f"Failed to create delegated credentials. {error_message(error)}") from error
    try:
        return discovery.build("people", "v1", credentials=credentials)
    except Exception as error:
        raise ActionFailure(f"Unable to create client. {error_message(error)}") from error


def normalize_mask(value, label):
    values = [part.strip() for part in value.split(",") if part.strip()]
    if not values:
        raise ActionFailure(INVALID_COMMA_SEPARATED_ERROR_MESSAGE.format(label))
    return ",".join(values)


def validate_limit(value):
    if value is None:
        return None
    try:
        if not float(value).is_integer():
            raise ValueError
        value = int(value)
    except (TypeError, ValueError, OverflowError) as error:
        raise ActionFailure(INVALID_INTEGER_ERROR_MESSAGE.format(LIMIT_KEY)) from error
    if value <= 0:
        raise ActionFailure(INVALID_NON_ZERO_NON_NEGATIVE_INTEGER_ERROR_MESSAGE.format(LIMIT_KEY))
    return value


def paginate(client, action_id, fields, limit):
    """Match legacy page size, truncation and pagination safety checks."""
    kwargs = {"pageSize": 1000}
    items = []
    page_token = None
    page_count = 0
    consecutive_empty_pages = 0
    seen_page_tokens = set()
    while True:
        if page_count >= 100:
            raise RuntimeError("Pagination stopped after reaching the safety limit of 100 pages")
        if page_token:
            kwargs["pageToken"] = page_token
        before = len(items)
        page_count += 1
        if action_id == "list_other_contacts":
            kwargs["readMask"] = fields
            response = client.otherContacts().list(**kwargs).execute()
            page_items = response.get("otherContacts")
        elif action_id == "list_directory":
            kwargs.update(sources=["DIRECTORY_SOURCE_TYPE_DOMAIN_CONTACT", "DIRECTORY_SOURCE_TYPE_DOMAIN_PROFILE"], readMask=fields)
            response = client.people().listDirectoryPeople(**kwargs).execute()
            page_items = response.get("people")
        else:
            kwargs.update(sources=["READ_SOURCE_TYPE_CONTACT"], personFields=fields)
            response = client.people().connections().list(resourceName="people/me", **kwargs).execute()
            page_items = response.get("connections")
        if page_items:
            items.extend(page_items)
        if limit and len(items) >= limit:
            return items[:limit]
        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break
        if len(items) >= 10000:
            raise RuntimeError("Pagination stopped after reaching the safety limit of 10000 items")
        if next_page_token in seen_page_tokens:
            raise RuntimeError("Pagination stopped because the API returned a repeated page token")
        if len(items) == before:
            consecutive_empty_pages += 1
            if consecutive_empty_pages >= 3:
                raise RuntimeError("Pagination stopped after the API returned 3 consecutive empty pages")
        else:
            consecutive_empty_pages = 0
        seen_page_tokens.add(next_page_token)
        page_token = next_page_token
    return items


def execute(request_factory, failure_message, include_unexpected_error=True):
    # Import at runtime for manifest generation; HttpError has special legacy messages.
    from googleapiclient.errors import HttpError

    try:
        return request_factory().execute()
    except HttpError as error:
        raise ActionFailure(f"{failure_message}. {error_message(error)}") from error
    except Exception as error:
        message = f"{failure_message}. {error_message(error)}" if include_unexpected_error else failure_message
        raise ActionFailure(message) from error
