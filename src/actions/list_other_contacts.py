# File: list_other_contacts.py
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
from soar_sdk.abstract import SOARClient
from soar_sdk.action_results import ActionOutput, OutputField, PermissiveActionOutput
from soar_sdk.exceptions import ActionFailure
from soar_sdk.params import Param

from ..app import Asset, app
from ..consts import GOOGLE_LIST_OTHER_CONTACTS_FAILED_MESSAGE, GOOGLE_OTHER_CONTACTS_SCOPE_READ_ONLY
from ..helper import create_client, error_message, normalize_mask, paginate, validate_limit
from ..models import LegacyParams, PersonOutput


class ListOtherContactsParams(LegacyParams):
    # Non-optional mask types preserve defaults; SDK Optional fields become None when omitted.
    read_mask: str = Param(
        required=False,
        description="Comma-separated list of fields to be returned for each person. If not provided, default values will be used",
        default="names,emailAddresses",
    )
    limit: float | None = Param(description="Number of contacts to include in the response")


class ListOtherContactsNamesMetadataSourceOutput(PermissiveActionOutput):
    id: str = OutputField(example_values=["6babaf04880e3563"])
    type: str = OutputField(example_values=["OTHER_CONTACT"])


class ListOtherContactsNamesMetadataOutput(PermissiveActionOutput):
    source: ListOtherContactsNamesMetadataSourceOutput = OutputField()
    primary: bool = OutputField(example_values=[True, False])


class ListOtherContactsNamesOutput(PermissiveActionOutput):
    metadata: ListOtherContactsNamesMetadataOutput = OutputField()
    givenName: str = OutputField(example_values=["Test user"])
    familyName: str = OutputField(example_values=["Test user"])
    displayName: str = OutputField(example_values=["Test user"], column_name="Display Name")
    unstructuredName: str = OutputField(example_values=["Test user"])
    displayNameLastFirst: str = OutputField(example_values=["Test, user"])
    middleName: str = OutputField(example_values=["Test user"])


class ListOtherContactsEmailAddressesMetadataSourceOutput(PermissiveActionOutput):
    id: str = OutputField(example_values=["6babaf04880e3563"])
    type: str = OutputField(example_values=["OTHER_CONTACT"])


class ListOtherContactsEmailAddressesMetadataOutput(PermissiveActionOutput):
    source: ListOtherContactsEmailAddressesMetadataSourceOutput = OutputField()
    primary: bool = OutputField(example_values=[True, False])


class ListOtherContactsEmailAddressesOutput(PermissiveActionOutput):
    value: str = OutputField(cef_types=["email"], example_values=["user@example.com"], column_name="Email")
    metadata: ListOtherContactsEmailAddressesMetadataOutput = OutputField()
    type: str = OutputField(example_values=["other"])
    formattedType: str = OutputField(example_values=["Other"])


class ListOtherContactsMetadataSourcesOutput(PermissiveActionOutput):
    id: str = OutputField(example_values=["6babaf04880e3563"])
    etag: str = OutputField(example_values=["#pFbf7+rr0xE="])
    type: str = OutputField(example_values=["OTHER_CONTACT"])
    updateTime: str = OutputField(example_values=["2017-05-24T23:40:54.632001Z"])


class ListOtherContactsMetadataOutput(PermissiveActionOutput):
    sources: list[ListOtherContactsMetadataSourcesOutput] = OutputField()
    objectType: str = OutputField(example_values=["PERSON"])


class ListOtherContactsOutput(PersonOutput):
    table_column_order = {
        "action_result.data.*.names.*.displayName": 2,
        "action_result.data.*.resourceName": 0,
        "action_result.data.*.emailAddresses.*.value": 1,
    }

    etag: str = OutputField(example_values=["%EgcBAj0JPjcuGgECIgxwRmJmNytycjB4RT0="])
    names: list[ListOtherContactsNamesOutput] = OutputField()
    resourceName: str = OutputField(
        cef_types=["googlepeople resource name"], example_values=["otherContacts/c7758487217073173859"], column_name="Resource Name"
    )
    emailAddresses: list[ListOtherContactsEmailAddressesOutput] = OutputField()
    metadata: ListOtherContactsMetadataOutput = OutputField()


class ListOtherContactsSummary(ActionOutput):
    total_other_contacts_returned: int = OutputField(alias="total_otherContacts_returned", example_values=[6])


@app.action(
    name="list other contacts",
    identifier="list_other_contacts",
    description="Lists all contacts that are not in a contact group",
    action_type="investigate",
    read_only=True,
    summary_type=ListOtherContactsSummary,
    verbose='This action lists all "Other contacts" which are contacts that are not in another contact group. These contacts are typically automatically created from interactions.',
    render_as="table",
)
def list_other_contacts(params: ListOtherContactsParams, soar: SOARClient, asset: Asset) -> list[ListOtherContactsOutput]:
    """Lists all contacts that are not in a contact group."""
    client = create_client(asset, [GOOGLE_OTHER_CONTACTS_SCOPE_READ_ONLY])
    fields = normalize_mask(params.read_mask, "read mask")
    limit = validate_limit(params.limit)
    try:
        records = paginate(client, "list_other_contacts", fields, limit)
    except Exception as error:
        raise ActionFailure(f"{GOOGLE_LIST_OTHER_CONTACTS_FAILED_MESSAGE}. {error_message(error)}") from error
    soar.set_summary(ListOtherContactsSummary(total_other_contacts_returned=len(records)))
    soar.set_message(f"Successfully retrieved {len(records)} otherContact{'' if len(records) == 1 else 's'}")
    return [ListOtherContactsOutput(**record) for record in records]
