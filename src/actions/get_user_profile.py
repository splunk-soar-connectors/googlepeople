# File: get_user_profile.py
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
from ..consts import GOOGLE_CONTACTS_SCOPE, GOOGLE_GET_USER_PROFILE_FAILED_MESSAGE, GOOGLE_PROFILE_SCOPE
from ..helper import create_client, execute, normalize_mask
from ..models import LegacyParams, PersonOutput


class GetUserProfileParams(LegacyParams):
    # Non-optional mask types preserve defaults; SDK Optional fields become None when omitted.
    resource_name: str = Param(
        description="Resource name of the person to provide info about", cef_types=["googlepeople resource name"], primary=True
    )
    person_fields: str = Param(
        required=False, description="Comma-separated list of fields to be returned for the person", default="names,emailAddresses"
    )


class GetUserProfileMetadataSourcesOutput(PermissiveActionOutput):
    id: str = OutputField(example_values=["7d369160095862fe"])
    etag: str = OutputField(example_values=["#JgTYM+ybUz4="])
    type: str = OutputField(example_values=["CONTACT"])
    updateTime: str = OutputField(example_values=["2020-08-04T23:06:55.492Z"])


class GetUserProfileMetadataOutput(PermissiveActionOutput):
    sources: list[GetUserProfileMetadataSourcesOutput] = OutputField()
    objectType: str = OutputField(example_values=["PERSON"])


class GetUserProfileNamesMetadataSourceOutput(PermissiveActionOutput):
    id: str = OutputField(example_values=["113211632970586460828"])
    type: str = OutputField(example_values=["PROFILE"], column_name="Source Type")


class GetUserProfileNamesMetadataOutput(PermissiveActionOutput):
    source: GetUserProfileNamesMetadataSourceOutput = OutputField()
    primary: bool = OutputField(example_values=[True, False])


class GetUserProfileNamesOutput(PermissiveActionOutput):
    middleName: str = OutputField(example_values=["Test user"])
    metadata: GetUserProfileNamesMetadataOutput = OutputField()
    givenName: str = OutputField(example_values=["Test user"])
    familyName: str = OutputField(example_values=["Test user"])
    displayName: str = OutputField(example_values=["Test user"], column_name="Display Name")
    unstructuredName: str = OutputField(example_values=["Test user"])
    displayNameLastFirst: str = OutputField(example_values=["Test, user"])
    honorificSuffix: str = OutputField(example_values=["Test"])


class GetUserProfileEmailAddressesMetadataSourceOutput(PermissiveActionOutput):
    id: str = OutputField(example_values=["116919555361086422724"])
    type: str = OutputField(example_values=["DOMAIN_PROFILE"], column_name="Email Address Source Type")


class GetUserProfileEmailAddressesMetadataOutput(PermissiveActionOutput):
    source: GetUserProfileEmailAddressesMetadataSourceOutput = OutputField()
    primary: bool = OutputField(example_values=[True, False])
    verified: bool = OutputField(example_values=[True, False])


class GetUserProfileEmailAddressesOutput(PermissiveActionOutput):
    type: str = OutputField(example_values=["other"])
    formattedType: str = OutputField(example_values=["Other"])
    value: str = OutputField(cef_types=["email"], example_values=["user@example.com"], column_name="Email")
    metadata: GetUserProfileEmailAddressesMetadataOutput = OutputField()


class GetUserProfileOutput(PersonOutput):
    table_column_order = {
        "action_result.data.*.names.*.metadata.source.type": 3,
        "action_result.data.*.names.*.displayName": 1,
        "action_result.data.*.resourceName": 0,
        "action_result.data.*.emailAddresses.*.value": 2,
        "action_result.data.*.emailAddresses.*.metadata.source.type": 4,
    }

    metadata: GetUserProfileMetadataOutput = OutputField()
    etag: str = OutputField(example_values=["%EgcBAj0JPjcuGgQBAgUH"])
    names: list[GetUserProfileNamesOutput] = OutputField()
    resourceName: str = OutputField(
        cef_types=["googlepeople resource name"], example_values=["people/113211632970586460828"], column_name="Resource Name"
    )
    emailAddresses: list[GetUserProfileEmailAddressesOutput] = OutputField()


class GetUserProfileSummary(ActionOutput):
    resource_id_returned: str | None = OutputField(example_values=["people/113211632970586460828"])


@app.action(
    name="get user profile",
    identifier="get_user_profile",
    description="Provides information about a person given account ID",
    action_type="investigate",
    read_only=True,
    summary_type=GetUserProfileSummary,
    render_as="table",
)
def get_user_profile(params: GetUserProfileParams, soar: SOARClient, asset: Asset) -> GetUserProfileOutput:
    """Provides information about a person given account ID."""
    if not params.resource_name.strip():
        raise ActionFailure("Required parameters are not specified or are blank: ['resource_name']")
    if params.resource_name.startswith("otherContacts/"):
        raise ActionFailure("This action cannot be performed on otherContacts")
    client = create_client(asset, [GOOGLE_PROFILE_SCOPE, GOOGLE_CONTACTS_SCOPE])
    fields = normalize_mask(params.person_fields, "person fields")
    response = execute(
        lambda: client.people().get(resourceName=params.resource_name, sources=["READ_SOURCE_TYPE_CONTACT"], personFields=fields),
        GOOGLE_GET_USER_PROFILE_FAILED_MESSAGE,
        include_unexpected_error=False,
    )
    soar.set_summary(GetUserProfileSummary(resource_id_returned=response.get("resourceName")))
    soar.set_message("Successfully retrieved user profile")
    return GetUserProfileOutput(**response)
