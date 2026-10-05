# File: list_directory.py
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
from ..consts import GOOGLE_DIRECTORY_SCOPE_READ_ONLY, GOOGLE_LIST_DIRECTORY_FAILED_MESSAGE
from ..helper import create_client, error_message, normalize_mask, paginate, validate_limit
from ..models import LegacyParams, PersonOutput
from ..views import render_list_directory


class ListDirectoryParams(LegacyParams):
    # Non-optional mask types preserve defaults; SDK Optional fields become None when omitted.
    read_mask: str = Param(
        required=False,
        description="Comma-separated list of fields to be returned for each person. If not provided, default values will be used",
        default="names,emailAddresses",
    )
    limit: float | None = Param(description="Number of responses to include in the response")


class ListDirectoryNamesMetadataSourceOutput(PermissiveActionOutput):
    id: str = OutputField(example_values=["7c6136a10b0a9c93"])
    type: str = OutputField(example_values=["CONTACT"])


class ListDirectoryNamesMetadataOutput(PermissiveActionOutput):
    source: ListDirectoryNamesMetadataSourceOutput = OutputField()
    primary: bool = OutputField(example_values=[True, False])


class ListDirectoryNamesOutput(PermissiveActionOutput):
    metadata: ListDirectoryNamesMetadataOutput = OutputField()
    givenName: str = OutputField(example_values=["Test user"])
    familyName: str = OutputField(example_values=["Test user"])
    displayName: str = OutputField(example_values=["Test user"])
    unstructuredName: str = OutputField(example_values=["Test user"])
    displayNameLastFirst: str = OutputField(example_values=["Test, user"])
    middleName: str = OutputField(example_values=["Test user"])


class ListDirectoryEmailAddressesMetadataSourceOutput(PermissiveActionOutput):
    id: str = OutputField(example_values=["117111371020715649097"])
    type: str = OutputField(example_values=["DOMAIN_PROFILE"])


class ListDirectoryEmailAddressesMetadataOutput(PermissiveActionOutput):
    source: ListDirectoryEmailAddressesMetadataSourceOutput = OutputField()
    primary: bool = OutputField(example_values=[True, False])
    verified: bool = OutputField(example_values=[True, False])


class ListDirectoryEmailAddressesOutput(PermissiveActionOutput):
    value: str = OutputField(cef_types=["email"], example_values=["user@example.com"])
    metadata: ListDirectoryEmailAddressesMetadataOutput = OutputField()
    type: str = OutputField(example_values=["work"])
    formattedType: str = OutputField(example_values=["Work"])


class ListDirectoryPhoneNumbersMetadataSourceOutput(PermissiveActionOutput):
    id: str = OutputField(example_values=["107701908237315216077"])
    type: str = OutputField(example_values=["DOMAIN_PROFILE"])


class ListDirectoryPhoneNumbersMetadataOutput(PermissiveActionOutput):
    source: ListDirectoryPhoneNumbersMetadataSourceOutput = OutputField()
    primary: bool = OutputField(example_values=[True])


class ListDirectoryPhoneNumbersOutput(PermissiveActionOutput):
    type: str = OutputField(example_values=["work"])
    value: str = OutputField()
    metadata: ListDirectoryPhoneNumbersMetadataOutput = OutputField()
    formattedType: str = OutputField(example_values=["Work"])


class ListDirectoryOutput(PersonOutput):
    etag: str = OutputField(example_values=["%EgcBAj0JPjcuGgMBBwg="])
    resourceName: str = OutputField(cef_types=["googlepeople resource name"], example_values=["people/113211632970586460828"])
    names: list[ListDirectoryNamesOutput] = OutputField()
    emailAddresses: list[ListDirectoryEmailAddressesOutput] = OutputField()
    phoneNumbers: list[ListDirectoryPhoneNumbersOutput] = OutputField()


class ListDirectorySummary(ActionOutput):
    total_people_returned: int = OutputField(example_values=[7])


@app.action(
    name="list directory",
    identifier="list_directory",
    description="Lists all contacts and profiles in the user's domain directory",
    action_type="investigate",
    read_only=True,
    summary_type=ListDirectorySummary,
    view_handler=render_list_directory,
)
def list_directory(params: ListDirectoryParams, soar: SOARClient, asset: Asset) -> list[ListDirectoryOutput]:
    """Lists all contacts and profiles in the user's domain directory."""
    client = create_client(asset, [GOOGLE_DIRECTORY_SCOPE_READ_ONLY])
    fields = normalize_mask(params.read_mask, "read mask")
    limit = validate_limit(params.limit)
    try:
        records = paginate(client, "list_directory", fields, limit)
    except Exception as error:
        raise ActionFailure(f"{GOOGLE_LIST_DIRECTORY_FAILED_MESSAGE}. {error_message(error)}") from error
    soar.set_summary(ListDirectorySummary(total_people_returned=len(records)))
    soar.set_message(f"Successfully retrieved {len(records)} {'person' if len(records) == 1 else 'people'}")
    return [ListDirectoryOutput(**record) for record in records]
