# Copyright (c) 2021-2026 Splunk Inc.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0

from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from google.oauth2 import service_account
from googleapiclient import discovery
from soar_sdk.exceptions import ActionFailure

from src import helper
from src.app import test_connectivity as connectivity
from src.consts import GOOGLE_CONTACTS_SCOPE
from tests.test_actions import request_for


@pytest.mark.parametrize(
    "action,key,extra",
    [
        (
            "list_people",
            "connections",
            {"resourceName": "people/me", "sources": ["READ_SOURCE_TYPE_CONTACT"], "personFields": "names,emailAddresses"},
        ),
        ("list_other_contacts", "otherContacts", {"readMask": "names,emailAddresses"}),
        (
            "list_directory",
            "people",
            {"sources": ["DIRECTORY_SOURCE_TYPE_DOMAIN_CONTACT", "DIRECTORY_SOURCE_TYPE_DOMAIN_PROFILE"], "readMask": "names,emailAddresses"},
        ),
    ],
)
def test_pagination_requests_and_truncation(action, key, extra):
    client = Mock()
    request = request_for(client, action)
    request.return_value.execute.side_effect = [
        {key: [{"resourceName": "a"}], "nextPageToken": "next"},
        {key: [{"resourceName": "b"}, {"resourceName": "c"}]},
    ]
    assert helper.paginate(client, action, "names,emailAddresses", 2) == [{"resourceName": "a"}, {"resourceName": "b"}]
    assert request.call_args_list[0].kwargs == {"pageSize": 1000, **extra}
    assert request.call_args_list[1].kwargs == {"pageSize": 1000, "pageToken": "next", **extra}


def test_repeated_page_token_is_rejected():
    client = Mock()
    request_for(client, "list_people").return_value.execute.return_value = {"connections": [{"resourceName": "a"}], "nextPageToken": "same"}
    with pytest.raises(RuntimeError, match="repeated page token"):
        helper.paginate(client, "list_people", "names", None)


def test_three_consecutive_empty_pages_are_rejected():
    client = Mock()
    request_for(client, "list_people").return_value.execute.side_effect = [{"nextPageToken": str(i)} for i in range(3)]
    with pytest.raises(RuntimeError, match="3 consecutive empty pages"):
        helper.paginate(client, "list_people", "names", None)


@pytest.mark.parametrize("items_per_page,expected_calls,message", [(1, 100, "100 pages"), (1000, 10, "10000 items")])
def test_pagination_safety_limits(items_per_page, expected_calls, message):
    client = Mock()
    request = request_for(client, "list_people")
    request.return_value.execute.side_effect = [{"connections": [{}] * items_per_page, "nextPageToken": str(i)} for i in range(101)]
    with pytest.raises(RuntimeError, match=message):
        helper.paginate(client, "list_people", "names", None)
    assert request.call_count == expected_calls


@pytest.mark.parametrize("value,expected", [(None, None), (1, 1), (2.0, 2), ("3", 3)])
def test_legacy_integer_validation(value, expected):
    assert helper.validate_limit(value) == expected


@pytest.mark.parametrize("value", ["a", "2.5", "3.0", {}, [], float("inf"), float("nan")])
def test_invalid_integer_validation(value):
    with pytest.raises(ActionFailure, match="valid integer"):
        helper.validate_limit(value)


def test_masks_are_trimmed_and_empty_segments_removed():
    assert helper.normalize_mask(" names, ,emailAddresses, ", "read mask") == "names,emailAddresses"


def test_delegated_service_account_authentication(monkeypatch):
    factory = Mock()
    build = Mock()
    monkeypatch.setattr(service_account.Credentials, "from_service_account_info", factory)
    monkeypatch.setattr(discovery, "build", build)
    asset = SimpleNamespace(key_json='{"client_email":"service@example.com"}', login_email="user@example.com")
    assert helper.create_client(asset, [GOOGLE_CONTACTS_SCOPE]) is build.return_value
    factory.assert_called_once_with({"client_email": "service@example.com"}, scopes=[GOOGLE_CONTACTS_SCOPE])
    factory.return_value.with_subject.assert_called_once_with("user@example.com")
    build.assert_called_once_with("people", "v1", credentials=factory.return_value.with_subject.return_value)


@pytest.mark.parametrize(
    "key_json,email,message", [("bad json", "user@example.com", "Contents of service account"), ("{}", "invalid", "Login email")]
)
def test_invalid_asset_configuration(key_json, email, message):
    with pytest.raises(ActionFailure, match=message):
        helper.create_client(SimpleNamespace(key_json=key_json, login_email=email), [GOOGLE_CONTACTS_SCOPE])


@pytest.mark.parametrize(
    "stage,message",
    [
        ("credentials", "Unable to get the credentials"),
        ("delegation", "Failed to create delegated credentials"),
        ("discovery", "Unable to create client"),
    ],
)
def test_authentication_failure_messages(stage, message, monkeypatch):
    factory = Mock()
    build = Mock()
    monkeypatch.setattr(service_account.Credentials, "from_service_account_info", factory)
    monkeypatch.setattr(discovery, "build", build)
    failing = {"credentials": factory, "delegation": factory.return_value.with_subject, "discovery": build}[stage]
    failing.side_effect = RuntimeError("Denied")
    with pytest.raises(ActionFailure, match=message):
        helper.create_client(SimpleNamespace(key_json="{}", login_email="user@example.com"), [GOOGLE_CONTACTS_SCOPE])


def test_connectivity_preserves_scopes_and_request(monkeypatch):
    import src.app as module

    client = Mock()
    create = Mock(return_value=client)
    monkeypatch.setattr(module, "create_client", create)
    logger = Mock()
    monkeypatch.setattr(module, "logger", logger)
    asset = SimpleNamespace(login_email="user@example.com")
    assert connectivity.__wrapped__(Mock(), asset) is None
    create.assert_called_once_with(asset, [GOOGLE_CONTACTS_SCOPE])
    request_for(client, "list_people").assert_called_once_with(resourceName="people/me", personFields="names,emailAddresses")
    logger.info.assert_any_call("Getting list of connections")
    assert all(asset.login_email not in str(call) for call in logger.mock_calls)


def test_connectivity_error_decoding(monkeypatch):
    import src.app as module

    client = Mock()
    request_for(client, "list_people").return_value.execute.side_effect = RuntimeError(r"Denied &amp; blocked\u0021")
    monkeypatch.setattr(module, "create_client", Mock(return_value=client))
    with pytest.raises(ActionFailure, match=r"Error while listing connections\. Error Message: Denied & blocked!"):
        connectivity.__wrapped__(Mock(), SimpleNamespace(login_email="user@example.com"))
