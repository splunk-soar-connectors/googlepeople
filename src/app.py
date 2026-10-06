# File: app.py
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
from html import unescape

from soar_sdk.abstract import SOARClient
from soar_sdk.app import App
from soar_sdk.asset import AssetField, BaseAsset, FieldCategory
from soar_sdk.exceptions import ActionFailure
from soar_sdk.logging import getLogger

from .consts import GOOGLE_CONTACTS_SCOPE
from .helper import create_client, error_message


logger = getLogger()


class Asset(BaseAsset):
    key_json: str = AssetField(description="Contents of service account JSON file", sensitive=True, category=FieldCategory.CONNECTIVITY)
    login_email: str = AssetField(description="Login email", category=FieldCategory.CONNECTIVITY)


app = App(
    name="Google People",
    app_type="identity management",
    logo="logo_googlepeople.svg",
    logo_dark="logo_googlepeople_dark.svg",
    product_vendor="Google",
    product_name="Google People",
    publisher="Splunk",
    appid="cfeed12d-b40f-477a-b9f9-59c37d12ebfe",
    python_version="3.13",
    fips_compliant=True,
    asset_cls=Asset,
)


@app.test_connectivity()
def test_connectivity(soar: SOARClient, asset: Asset) -> None:
    """Validate the asset configuration for connectivity using supplied configuration."""
    logger.info("Creating Google People client...")
    try:
        client = create_client(asset, [GOOGLE_CONTACTS_SCOPE])
    except ActionFailure:
        logger.info("Test Connectivity Failed")
        raise
    logger.info("Getting list of connections")
    try:
        client.people().connections().list(resourceName="people/me", personFields="names,emailAddresses").execute()
    except Exception as error:
        # BeautifulSoup is a runtime dependency; retain the legacy error decoding.
        from bs4 import UnicodeDammit

        logger.info("Test Connectivity Failed")
        message = unescape(UnicodeDammit(error_message(error)).unicode_markup.encode("utf-8").decode("unicode_escape"))
        raise ActionFailure(f"Error while listing connections. {message}") from error
    logger.info("Test Connectivity Passed")


from .actions import copy_contact, get_user_profile, list_directory, list_other_contacts, list_people, make_request  # noqa: F401


if __name__ == "__main__":
    app.cli()
