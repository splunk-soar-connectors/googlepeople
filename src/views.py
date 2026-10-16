# File: views.py
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
from soar_sdk.action_results import PermissiveActionOutput

from .app import app


def view_context(output):
    return {"results": [{"data": [item.model_dump(by_alias=True) for item in output]}]}


@app.view_handler(template="googlepeople_copy_contact.html")
def render_copy_contact(output: list[PermissiveActionOutput]) -> dict:
    return view_context(output)


@app.view_handler(template="googlepeople_list_directory.html")
def render_list_directory(output: list[PermissiveActionOutput]) -> dict:
    return view_context(output)
