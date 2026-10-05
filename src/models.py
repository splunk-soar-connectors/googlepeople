# File: models.py
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
from typing import ClassVar

from pydantic import PrivateAttr
from soar_sdk.action_results import PermissiveActionOutput
from soar_sdk.params import Params


class PersonOutput(PermissiveActionOutput):
    """Preserve raw Google responses while exposing legacy SOAR metadata."""

    table_column_order: ClassVar[dict[str, int]] = {}

    @classmethod
    def _to_json_schema(cls, parent_datapath="action_result.data.*", column_order_counter=None):
        # SDK traversal groups nested fields. Legacy columns interleave names and
        # email metadata, so declaration order alone cannot preserve their order.
        for field in super()._to_json_schema(parent_datapath, column_order_counter):
            if field["data_path"] in cls.table_column_order:
                field["column_order"] = cls.table_column_order[field["data_path"]]
            yield field


class LegacyParams(Params):
    """Echo the caller's parameter keys while applying defaults for API calls."""

    _provided_keys: set[str] = PrivateAttr(default_factory=set)

    def __init__(self, **values):
        # SDK Optional validation inserts None fields. Capture keys first so the
        # action_result.parameter echo matches the legacy ActionResult(dict(param)).
        provided_keys = set(values)
        super().__init__(**values)
        self._provided_keys = provided_keys

    def model_dump(self, *args, **kwargs):
        kwargs.setdefault("include", self._provided_keys)
        return super().model_dump(*args, **kwargs)
