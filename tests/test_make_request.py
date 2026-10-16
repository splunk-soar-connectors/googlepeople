# Copyright (c) 2026 Splunk Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Exercise make_request's Google Auth transport without external requests."""

from importlib import import_module
from types import SimpleNamespace
from unittest.mock import Mock

from google.auth.credentials import Credentials
from requests import Response, Session

from src.app import app
from src.consts import GOOGLE_CONTACTS_SCOPE


def test_make_request_refreshes_and_sends_authorized_request(monkeypatch):
    module = import_module("src.actions.make_request")
    handler = app.get_actions()["make_request"]
    calls = []

    class RefreshingCredentials(Credentials):
        def refresh(self, request):
            token_response = request(url="https://oauth2.googleapis.com/token", method="POST")
            assert token_response.status == 200
            self.token = "test-access-token"

    credentials = RefreshingCredentials()
    create = Mock(return_value=credentials)
    monkeypatch.setattr(module, "create_credentials", create)

    def fake_request(self, method, url, **kwargs):
        calls.append((method, url, kwargs))
        response = Response()
        response.status_code = 200
        response._content = b'{"connections":[]}'
        response.url = url
        return response

    monkeypatch.setattr(Session, "request", fake_request)
    asset = SimpleNamespace()
    params = handler.params_class(
        http_method="GET",
        endpoint="/v1/people/me/connections",
        query_parameters='{"personFields":"names"}',
        timeout=17,
    )
    result = handler.__wrapped__(params, asset)

    create.assert_called_once_with(asset, [GOOGLE_CONTACTS_SCOPE])
    assert [(method, url) for method, url, _ in calls] == [
        ("POST", "https://oauth2.googleapis.com/token"),
        ("GET", "https://people.googleapis.com/v1/people/me/connections"),
    ]
    assert calls[0][2]["timeout"] == 17
    assert calls[1][2]["timeout"] == 17
    api_headers = {key.lower(): value for key, value in calls[1][2]["headers"].items()}
    assert api_headers["authorization"] == "Bearer test-access-token"
    assert calls[1][2]["params"] == {"personFields": "names"}
    assert result.status_code == 200
    assert result.response_body == '{"connections":[]}'
