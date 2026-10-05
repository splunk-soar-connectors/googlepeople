# File: copy_contact.py
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
from ..consts import (
    GOOGLE_CONTACTS_SCOPE,
    GOOGLE_COPY_CONTACT_FAILED_MESSAGE,
    GOOGLE_OTHER_CONTACTS_SCOPE_READ_ONLY,
    OTHER_CONTACTS_RESOURCE_NAME_PREFIX,
)
from ..helper import create_client, execute, normalize_mask
from ..models import LegacyParams, PersonOutput
from ..views import render_copy_contact


class CopyContactParams(LegacyParams):
    # Non-optional mask types preserve defaults; SDK Optional fields become None when omitted.
    resource_name: str = Param(
        description='Resource name of the "Other contact" to copy', cef_types=["googlepeople resource name"], primary=True
    )
    copy_mask: str = Param(
        required=False,
        description="Comma-separated list of fields to be copied into the new contact",
        default="names,emailAddresses,phoneNumbers",
    )


class CopyContactMetadataSourcesProfileMetadataOutput(PermissiveActionOutput):
    userTypes: str = OutputField(example_values=["GOOGLE_USER"])
    objectType: str = OutputField(example_values=["PERSON"])


class CopyContactMetadataSourcesOutput(PermissiveActionOutput):
    id: str = OutputField(example_values=["59b7075988160d30"])
    etag: str = OutputField(example_values=["#diNkOxGfnAU="])
    type: str = OutputField(example_values=["CONTACT"])
    updateTime: str = OutputField(example_values=["2020-07-27T17:48:29.240Z"])
    profileMetadata: CopyContactMetadataSourcesProfileMetadataOutput = OutputField()


class CopyContactMetadataOutput(PermissiveActionOutput):
    sources: list[CopyContactMetadataSourcesOutput] = OutputField()
    objectType: str = OutputField(example_values=["PERSON"])


class CopyContactMembershipsMetadataSourceOutput(PermissiveActionOutput):
    id: str = OutputField(example_values=["59b7075988160d30"])
    type: str = OutputField(example_values=["CONTACT"])


class CopyContactMembershipsMetadataOutput(PermissiveActionOutput):
    source: CopyContactMembershipsMetadataSourceOutput = OutputField()


class CopyContactMembershipsContactGroupMembershipOutput(PermissiveActionOutput):
    contactGroupId: str = OutputField(example_values=["myContacts"])
    contactGroupResourceName: str = OutputField(example_values=["contactGroups/myContacts"])


class CopyContactMembershipsDomainMembershipOutput(PermissiveActionOutput):
    inViewerDomain: bool = OutputField(example_values=[True, False])


class CopyContactMembershipsOutput(PermissiveActionOutput):
    metadata: CopyContactMembershipsMetadataOutput = OutputField()
    contactGroupMembership: CopyContactMembershipsContactGroupMembershipOutput = OutputField()
    domainMembership: CopyContactMembershipsDomainMembershipOutput = OutputField()


class CopyContactPhoneNumbersMetadataSourceOutput(PermissiveActionOutput):
    id: str = OutputField(example_values=["36f9f3a8888aca24"])
    type: str = OutputField(example_values=["CONTACT"])


class CopyContactPhoneNumbersMetadataOutput(PermissiveActionOutput):
    source: CopyContactPhoneNumbersMetadataSourceOutput = OutputField()
    primary: bool = OutputField(example_values=[True, False])


class CopyContactPhoneNumbersOutput(PermissiveActionOutput):
    value: str = OutputField()
    metadata: CopyContactPhoneNumbersMetadataOutput = OutputField()
    canonicalForm: str = OutputField()


class CopyContactEmailAddressesMetadataSourceOutput(PermissiveActionOutput):
    id: str = OutputField(example_values=["59b7075988160d30"])
    type: str = OutputField(example_values=["CONTACT"])


class CopyContactEmailAddressesMetadataOutput(PermissiveActionOutput):
    verified: bool = OutputField(example_values=[True, False])
    source: CopyContactEmailAddressesMetadataSourceOutput = OutputField()
    primary: bool = OutputField(example_values=[True, False])


class CopyContactEmailAddressesOutput(PermissiveActionOutput):
    metadata: CopyContactEmailAddressesMetadataOutput = OutputField()
    value: str = OutputField(cef_types=["email"], example_values=["user@example.com"])
    type: str = OutputField(example_values=["other"])
    formattedType: str = OutputField(example_values=["Other"])


class CopyContactNamesMetadataSourceOutput(PermissiveActionOutput):
    id: str = OutputField(example_values=["71d4a4d58a0990ed"])
    type: str = OutputField(example_values=["CONTACT"])


class CopyContactNamesMetadataOutput(PermissiveActionOutput):
    source: CopyContactNamesMetadataSourceOutput = OutputField()
    primary: bool = OutputField(example_values=[True, False])


class CopyContactNamesOutput(PermissiveActionOutput):
    metadata: CopyContactNamesMetadataOutput = OutputField()
    givenName: str = OutputField(example_values=["Test user"])
    familyName: str = OutputField(example_values=["Test user"])
    displayName: str = OutputField(example_values=["Test user"])
    unstructuredName: str = OutputField(example_values=["Test user"])
    displayNameLastFirst: str = OutputField(example_values=["Test, user"])
    middleName: str = OutputField(example_values=["Test user"])


class CopyContactOutput(PersonOutput):
    etag: str = OutputField(example_values=["%EgcBAj0JPjcuGgQBAgUHIgxkaU5rT3hHZm5BVT0="])
    metadata: CopyContactMetadataOutput = OutputField()
    memberships: list[CopyContactMembershipsOutput] = OutputField()
    resourceName: str = OutputField(cef_types=["googlepeople resource name"], example_values=["people/c6464643871230266672"])
    phoneNumbers: list[CopyContactPhoneNumbersOutput] = OutputField()
    emailAddresses: list[CopyContactEmailAddressesOutput] = OutputField()
    names: list[CopyContactNamesOutput] = OutputField()


class CopyContactSummary(ActionOutput):
    total_contacts_copied: int = OutputField(example_values=[1])


@app.action(
    name="copy contact",
    identifier="copy_contact",
    description="Copy 'Other contact' to 'myContacts' group",
    action_type="generic",
    read_only=False,
    summary_type=CopyContactSummary,
    view_handler=render_copy_contact,
)
def copy_contact(params: CopyContactParams, soar: SOARClient, asset: Asset) -> CopyContactOutput:
    """Copy 'Other contact' to 'myContacts' group."""
    client = create_client(asset, [GOOGLE_CONTACTS_SCOPE, GOOGLE_OTHER_CONTACTS_SCOPE_READ_ONLY])
    if OTHER_CONTACTS_RESOURCE_NAME_PREFIX not in params.resource_name:
        raise ActionFailure("Resource name of contact to be copied must be 'otherContact'")
    fields = normalize_mask(params.copy_mask, "copy mask")
    response = execute(
        lambda: client.otherContacts().copyOtherContactToMyContactsGroup(resourceName=params.resource_name, body={"copyMask": fields}),
        GOOGLE_COPY_CONTACT_FAILED_MESSAGE,
        include_unexpected_error=False,
    )
    soar.set_summary(CopyContactSummary(total_contacts_copied=1))
    soar.set_message("Successfully copied 1 contact")
    return CopyContactOutput(**response)
