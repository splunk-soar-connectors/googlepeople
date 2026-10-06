# File: list_people.py
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
from ..consts import GOOGLE_CONTACTS_SCOPE, GOOGLE_LIST_PEOPLE_FAILED_MESSAGE
from ..helper import create_client, error_message, normalize_mask, paginate, validate_limit
from ..models import LegacyParams, PersonOutput


class ListPeopleParams(LegacyParams):
    # Non-optional mask types preserve defaults; SDK Optional fields become None when omitted.
    person_fields: str = Param(
        required=False,
        description="Comma-separated list of fields to be returned for each person. If not provided, default values will be used",
        default="names,emailAddresses",
    )
    limit: float | None = Param(description="Number of connections to include in the response")


class ListPeopleNamesMetadataSourceOutput(PermissiveActionOutput):
    id: str = OutputField(example_values=["7c6136a10b0a9c93"])
    type: str = OutputField(example_values=["CONTACT"])


class ListPeopleNamesMetadataOutput(PermissiveActionOutput):
    source: ListPeopleNamesMetadataSourceOutput = OutputField()
    primary: bool = OutputField(example_values=[True, False])


class ListPeopleNamesOutput(PermissiveActionOutput):
    metadata: ListPeopleNamesMetadataOutput = OutputField()
    givenName: str = OutputField(example_values=["Test user"])
    familyName: str = OutputField(example_values=["Test user"])
    displayName: str = OutputField(example_values=["Test user"], column_name="Display Name")
    unstructuredName: str = OutputField(example_values=["Test user"])
    displayNameLastFirst: str = OutputField(example_values=["Test, user"])
    middleName: str = OutputField(example_values=["Test user"])


class ListPeopleEmailAddressesMetadataSourceOutput(PermissiveActionOutput):
    id: str = OutputField(example_values=["57180f240cc67e88"])
    type: str = OutputField(example_values=["CONTACT"])


class ListPeopleEmailAddressesMetadataOutput(PermissiveActionOutput):
    source: ListPeopleEmailAddressesMetadataSourceOutput = OutputField()
    primary: bool = OutputField(example_values=[True, False])


class ListPeopleEmailAddressesOutput(PermissiveActionOutput):
    type: str = OutputField(example_values=["work"])
    formattedType: str = OutputField(example_values=["Work"])
    value: str = OutputField(cef_types=["email"], example_values=["user@example.com"], column_name="Email")
    metadata: ListPeopleEmailAddressesMetadataOutput = OutputField()


class ListPeopleMetadataSourcesOutput(PermissiveActionOutput):
    id: str = OutputField(example_values=["26162f4b8f0439b6"])
    etag: str = OutputField(example_values=["#G/xJmvdEqkU="])
    type: str = OutputField(example_values=["CONTACT"])
    updateTime: str = OutputField(example_values=["2020-11-27T05:26:14.900Z"])


class ListPeopleMetadataOutput(PermissiveActionOutput):
    sources: list[ListPeopleMetadataSourcesOutput] = OutputField()
    objectType: str = OutputField(example_values=["PERSON"])


class ListPeopleBirthdaysDateOutput(PermissiveActionOutput):
    day: float = OutputField(example_values=[1])
    year: float = OutputField(example_values=[1990])
    month: float = OutputField(example_values=[1])


class ListPeopleBirthdaysMetadataSourceOutput(PermissiveActionOutput):
    id: str = OutputField(example_values=["75b1dd3c0f20cb95"])
    type: str = OutputField(example_values=["CONTACT"])


class ListPeopleBirthdaysMetadataOutput(PermissiveActionOutput):
    source: ListPeopleBirthdaysMetadataSourceOutput = OutputField()
    primary: bool = OutputField(example_values=[True])


class ListPeopleBirthdaysOutput(PermissiveActionOutput):
    date: ListPeopleBirthdaysDateOutput = OutputField()
    text: str = OutputField(example_values=["1990-01-01"])
    metadata: ListPeopleBirthdaysMetadataOutput = OutputField()


class ListPeopleOutput(PersonOutput):
    table_column_order = {
        "action_result.data.*.names.*.displayName": 2,
        "action_result.data.*.resourceName": 0,
        "action_result.data.*.emailAddresses.*.value": 1,
    }

    names: list[ListPeopleNamesOutput] = OutputField()
    etag: str = OutputField(example_values=["%EgcBAj0JPjcuGgQBAgUHIgxYcEJzUVA3cmlaWT0="])
    resourceName: str = OutputField(
        cef_types=["googlepeople resource name"], example_values=["people/c6275782728248360584"], column_name="Resource Name"
    )
    emailAddresses: list[ListPeopleEmailAddressesOutput] = OutputField()
    metadata: ListPeopleMetadataOutput = OutputField()
    birthdays: list[ListPeopleBirthdaysOutput] = OutputField()


class ListPeopleSummary(ActionOutput):
    total_people_returned: int = OutputField(example_values=[1])


@app.action(
    name="list people",
    identifier="list_people",
    description="Lists authenticated user's contacts",
    action_type="investigate",
    read_only=True,
    summary_type=ListPeopleSummary,
    render_as="table",
)
def list_people(params: ListPeopleParams, soar: SOARClient, asset: Asset) -> list[ListPeopleOutput]:
    """Lists authenticated user's contacts."""
    client = create_client(asset, [GOOGLE_CONTACTS_SCOPE])
    fields = normalize_mask(params.person_fields, "person fields")
    limit = validate_limit(params.limit)
    try:
        records = paginate(client, "list_people", fields, limit)
    except Exception as error:
        raise ActionFailure(f"{GOOGLE_LIST_PEOPLE_FAILED_MESSAGE}. {error_message(error)}") from error
    soar.set_summary(ListPeopleSummary(total_people_returned=len(records)))
    soar.set_message(f"Successfully retrieved {len(records)} user{'' if len(records) == 1 else 's'}")
    return [ListPeopleOutput(**record) for record in records]
