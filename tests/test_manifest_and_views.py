# Copyright (c) 2021-2026 Splunk Inc.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0

import json
from pathlib import Path

import pytest
from soar_sdk.action_results import PermissiveActionOutput
from soar_sdk.views.template_renderer import JinjaTemplateRenderer

from src.app import Asset, app
from src.views import view_context


LEGACY = json.loads((Path(__file__).parent / "fixtures/legacy_manifest.json").read_text())
ROOT = Path(__file__).parent.parent


def test_app_identity_and_supported_runtime():
    assert app.app_meta_info["appid"] == LEGACY["appid"]
    assert app.app_meta_info["name"] == LEGACY["name"]
    assert app.app_meta_info["python_version"] == "3.13"
    assert app.app_meta_info["min_phantom_version"] == "7.0.0"
    assert app.app_meta_info["fips_compliant"] == LEGACY["fips_compliant"]
    assert Asset.fields_requiring_decryption() == {"key_json"}


def test_all_legacy_actions_registered():
    assert set(app.get_actions()) == {a["identifier"] for a in LEGACY["actions"]} | {"make_request"}


@pytest.mark.parametrize("legacy", LEGACY["actions"], ids=lambda action: action["identifier"])
def test_manifest_contract(legacy):
    actual = app.get_actions()[legacy["identifier"]].meta.model_dump()
    for key in ["action", "identifier", "type", "read_only", "versions"]:
        assert actual[key] == legacy[key]
    assert set(actual["parameters"]) == set(legacy["parameters"])
    for name, expected in legacy["parameters"].items():
        param = actual["parameters"][name]
        for key, default in [("required", False), ("primary", False), ("contains", [])]:
            assert param.get(key, default) == expected.get(key, default)
        for key in ["description", "data_type", "order"]:
            assert param[key] == expected[key]
        assert param.get("default") == expected.get("default")
    outputs = {f["data_path"]: f for f in actual["output"]}
    expected_paths = {f["data_path"] for f in legacy["output"]}
    if legacy["identifier"] == "test_connectivity":
        expected_paths = {"action_result.status", "action_result.message", "summary.total_objects", "summary.total_objects_successful"}
    assert set(outputs) == expected_paths
    for expected in legacy["output"]:
        output = outputs[expected["data_path"]]
        for key, default in [("contains", []), ("column_name", None), ("column_order", None)]:
            assert output.get(key, default) == expected.get(key, default)
        assert output["data_type"] == expected["data_type"]
    if legacy.get("render"):
        assert actual["render"]["type"] == legacy["render"]["type"]


@pytest.mark.parametrize(
    "template,headers",
    [
        ("googlepeople_copy_contact.html", ["Resource Name", "Email", "Phone Number", "Contact Group Resource Name"]),
        ("googlepeople_list_directory.html", ["Resource Name", "Email"]),
    ],
)
def test_custom_views_headers_and_escaping(template, headers):
    renderer = JinjaTemplateRenderer(str(ROOT / "templates"))
    person = PermissiveActionOutput(
        resourceName="people/123",
        emailAddresses=[{"value": "o'hara@example.com", "metadata": {"source": {"type": "CONTACT"}}}],
        names=[{"displayName": "<script>alert(1)</script>"}],
    )
    html = renderer.render_template(template, {**view_context([person]), "container": 12})
    positions = [html.index(f"<th>{header}</th>") for header in headers]
    assert positions == sorted(positions)
    assert 'class="googlepeople"' in html
    assert "people/123" in html
    assert "o&#39;hara@example.com" in html
    assert "<script>alert(1)</script>" not in html
    assert "\\u0027" in html
    assert "0, 12, null, false" in html


@pytest.mark.parametrize("template", ["googlepeople_copy_contact.html", "googlepeople_list_directory.html"])
def test_empty_custom_views(template):
    renderer = JinjaTemplateRenderer(str(ROOT / "templates"))
    html = renderer.render_template(template, {**view_context([]), "container": 12})
    assert "No data found" in html


@pytest.mark.parametrize("template", ["googlepeople_copy_contact.html", "googlepeople_list_directory.html"])
@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"resourceName": None, "emailAddresses": None, "memberships": None},
        {"emailAddresses": [{}]},
        {"emailAddresses": [{"value": "sample@example.com", "metadata": {}}]},
        {"emailAddresses": [{"metadata": {"source": {"type": "CONTACT"}}}]},
    ],
)
def test_custom_views_tolerate_missing_and_null_values(template, payload):
    renderer = JinjaTemplateRenderer(str(ROOT / "templates"))
    html = renderer.render_template(template, {**view_context([PermissiveActionOutput(**payload)]), "container": 12})
    assert 'class="googlepeople"' in html
    assert "<th>Resource Name</th>" in html
