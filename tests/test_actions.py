# Copyright (c) 2021-2026 Splunk Inc.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0

import importlib
import json
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from googleapiclient.errors import HttpError
from httplib2 import Response
from soar_sdk.exceptions import ActionFailure

from src.app import app


FIXTURES = json.loads((Path(__file__).parent / "fixtures/legacy_results.json").read_text())


def request_for(client, action):
    if action == "list_people":
        return client.people.return_value.connections.return_value.list
    if action == "list_directory":
        return client.people.return_value.listDirectoryPeople
    if action == "list_other_contacts":
        return client.otherContacts.return_value.list
    if action == "copy_contact":
        return client.otherContacts.return_value.copyOtherContactToMyContactsGroup
    return client.people.return_value.get


@pytest.mark.parametrize("case", FIXTURES["cases"], ids=lambda case: case["id"])
def test_complete_results_match_executed_legacy_handlers(case, monkeypatch):
    """Compare data, summaries, messages, scopes and API kwargs to legacy results."""
    action = case["action"]
    module = importlib.import_module(f"src.actions.{action}")
    handler = app.get_actions()[action]
    client = Mock()
    request = request_for(client, action)
    api = deepcopy(case["api"])
    request.return_value.execute.return_value = api
    create = Mock(return_value=client)
    monkeypatch.setattr(module, "create_client", create)
    soar = Mock()
    params = handler.params_class(**case["params"])
    result = handler.__wrapped__(params, soar, SimpleNamespace())
    data = result if isinstance(result, list) else [result]
    serialized = {
        "data": [item.model_dump(by_alias=True) for item in data],
        "summary": soar.set_summary.call_args.args[0].model_dump(by_alias=True),
        "message": soar.set_message.call_args.args[0],
        "status": True,
    }
    assert serialized == case["expected"]
    # Exercise the actual SDK result adapter, including parameter echo and list flattening.
    manager = Mock()
    app._adapt_action_result(result, manager, params, serialized["message"], soar.set_summary.call_args.args[0])
    platform_result = manager.add_result.call_args.args[0]
    assert {
        "data": platform_result.get_data(),
        "summary": platform_result.get_summary(),
        "message": platform_result.get_message(),
        "status": platform_result.get_status(),
        "parameter": platform_result.get_param(),
    } == {**case["expected"], "parameter": case["params"]}
    assert api == case["api"], "Model construction must not insert missing fields into the API payload"
    assert create.call_args.args[1] == case["scopes"]
    assert request.call_args.kwargs == case["request"]


@pytest.mark.parametrize("action", ["list_people", "list_directory", "list_other_contacts"])
def test_empty_list_and_default_mask(action, monkeypatch):
    module = importlib.import_module(f"src.actions.{action}")
    handler = app.get_actions()[action]
    client = Mock()
    request = request_for(client, action)
    request.return_value.execute.return_value = {}
    monkeypatch.setattr(module, "create_client", Mock(return_value=client))
    soar = Mock()
    assert handler.__wrapped__(handler.params_class(), soar, SimpleNamespace()) == []
    assert list(soar.set_summary.call_args.args[0].model_dump(by_alias=True).values()) == [0]
    assert "names,emailAddresses" in request.call_args.kwargs.values()


@pytest.mark.parametrize("action", ["list_people", "list_directory", "list_other_contacts"])
@pytest.mark.parametrize("limit", [0, -1, 0.5, float("inf"), float("nan")])
def test_invalid_limits_stop_before_api_request(action, limit, monkeypatch):
    module = importlib.import_module(f"src.actions.{action}")
    handler = app.get_actions()[action]
    client = Mock()
    monkeypatch.setattr(module, "create_client", Mock(return_value=client))
    with pytest.raises(ActionFailure, match="Please provide a valid"):
        handler.__wrapped__(handler.params_class(limit=limit), Mock(), SimpleNamespace())
    request_for(client, action).assert_not_called()


@pytest.mark.parametrize("action", list(app.get_actions().keys())[1:])
def test_empty_masks_are_rejected(action, monkeypatch):
    module = importlib.import_module(f"src.actions.{action}")
    handler = app.get_actions()[action]
    monkeypatch.setattr(module, "create_client", Mock(return_value=Mock()))
    field = (
        "copy_mask" if action == "copy_contact" else ("read_mask" if action in ["list_directory", "list_other_contacts"] else "person_fields")
    )
    params = {field: " , , "}
    if "resource_name" in handler.params_class.model_fields:
        params["resource_name"] = "otherContacts/123" if action == "copy_contact" else "people/123"
    with pytest.raises(ActionFailure, match="comma-seprated"):
        handler.__wrapped__(handler.params_class(**params), Mock(), SimpleNamespace())


@pytest.mark.parametrize(
    "action,resource,message",
    [
        ("get_user_profile", "otherContacts/123", "cannot be performed"),
        ("copy_contact", "people/123", "must be 'otherContact'"),
    ],
)
def test_invalid_resource_names(action, resource, message, monkeypatch):
    module = importlib.import_module(f"src.actions.{action}")
    handler = app.get_actions()[action]
    client = Mock()
    create = Mock(return_value=client)
    monkeypatch.setattr(module, "create_client", create)
    with pytest.raises(ActionFailure, match=message):
        handler.__wrapped__(handler.params_class(resource_name=resource), Mock(), SimpleNamespace())
    request_for(client, action).assert_not_called()
    if action == "get_user_profile":
        create.assert_not_called()


@pytest.mark.parametrize("resource", ["", " ", "\t\r\n", "\u00a0"])
def test_blank_profile_resource_names_fail_before_client_creation(resource, monkeypatch):
    module = importlib.import_module("src.actions.get_user_profile")
    handler = app.get_actions()["get_user_profile"]
    create = Mock()
    monkeypatch.setattr(module, "create_client", create)
    soar = Mock()
    with pytest.raises(ActionFailure, match="Required parameters are not specified or are blank"):
        handler.__wrapped__(handler.params_class(resource_name=resource), soar, SimpleNamespace())
    create.assert_not_called()
    soar.set_summary.assert_not_called()
    soar.set_message.assert_not_called()


@pytest.mark.parametrize("action", list(app.get_actions().keys())[1:])
@pytest.mark.parametrize("http_error", [False, True])
def test_api_errors_keep_legacy_messages(action, http_error, monkeypatch):
    module = importlib.import_module(f"src.actions.{action}")
    handler = app.get_actions()[action]
    client = Mock()
    error = HttpError(Response({"status": "403"}), b'{"error":{"message":"Denied"}}') if http_error else RuntimeError("Denied")
    request_for(client, action).return_value.execute.side_effect = error
    monkeypatch.setattr(module, "create_client", Mock(return_value=client))
    params = {}
    if "resource_name" in handler.params_class.model_fields:
        params["resource_name"] = "otherContacts/123" if action == "copy_contact" else "people/123"
    soar = Mock()
    with pytest.raises(ActionFailure, match="Failed to") as raised:
        handler.__wrapped__(handler.params_class(**params), soar, SimpleNamespace())
    if http_error:
        assert "Unable to parse the error message" in str(raised.value)
    else:
        assert ("Denied" in str(raised.value)) == action.startswith("list_")
    soar.set_summary.assert_not_called()
    soar.set_message.assert_not_called()


@pytest.mark.parametrize("action", ["list_people", "list_directory", "list_other_contacts"])
def test_omitted_parameters_are_not_added_to_echo(action):
    params = app.get_actions()[action].params_class()
    assert params.model_dump() == {}
    assert params.limit is None
    assert any(getattr(params, field) == "names,emailAddresses" for field in ["person_fields", "read_mask"] if hasattr(params, field))
