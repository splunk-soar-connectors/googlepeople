[comment]: # "Auto-generated SOAR connector documentation"
# Google People

Publisher: Splunk  
Connector Version: 1\.1\.2  
Product Vendor: Google  
Product Name: Google People  
Product Version Supported (regex): "\.\*"  
Minimum Product Version: 5\.0\.0  

This app integrates with Google People to support various generic and investigative actions

[comment]: # " File: readme.md"
[comment]: # "  Copyright (c) 2021-2022 Splunk Inc."
[comment]: # ""
[comment]: # "  Licensed under Apache 2.0 (https://www.apache.org/licenses/LICENSE-2.0.txt)"
[comment]: # ""
## SDK and SDK Licensing details for the app

#### cachetools

This app uses the cachetools module, which is licensed under the MIT License (MIT), Copyright (c)
2014-2020 Thomas Kemmer.

#### google-api-python-client

This app uses the google-api-python-client module, which is licensed under the Apache Software
License (Apache 2.0), Copyright (c) Google LLC.

#### google-auth-httplib2

This app uses the google-auth-httplib2 module, which is licensed under the Apache Software License
(Apache 2.0), Copyright (c) Google Cloud Platform.

#### google-auth-oauthlib

This app uses the google-auth-oauthlib module, which is licensed under the Apache Software License
(Apache 2.0), Copyright (c) Google Cloud Platform.

#### google-auth

This app uses the google-auth module, which is licensed under the Apache Software License (Apache
2.0), Copyright (c) Google Cloud Platform.

#### httplib2

This app uses the httplib2 module, which is licensed under the MIT License (MIT), Copyright (c) Joe
Gregorio.

#### oauth2client

This app uses the oauth2client module, which is licensed under the Apache Software License (Apache
2.0), Copyright (c) Google Inc.

#### pyasn1-modules

This app uses the pyasn1-modules module, which is licensed under the BSD License (BSD-2-Clause),
Copyright (c) Ilya Etingof.

#### rsa

This app uses the rsa module, which is licensed under the Apache Software License (ASL 2), Copyright
(c) Sybren A. Stuvel.

#### uritemplate

This app uses the uritemplate module, which is licensed under the OSI Approved, Apache Software
License, BSD License (BSD 3-Clause License or Apache License, Version 2.0), Copyright (c) Ian
Stapleton Cordasco.

### Service Account

This app requires a pre-configured service account to operate. Please follow the procedure outlined
at [this link](https://support.google.com/a/answer/7378726?hl=en) to create a service account.  
The following APIs will need to be enabled:

-   AdminSDK
-   Google People API

At the end of the creation process, the admin console should ask you to save the config as a JSON
file. Copy the contents of the JSON file in the clipboard and paste it as the value of the "Contents
of Service Account JSON file" asset configuration parameter.

### Scopes

Once the service account has been created and APIs enabled, the next step is to configure scopes on
these APIs to allow the App to access them. Every action requires different scopes to operate, these
are listed in the action documentation.  
To enable scopes please complete the following steps:

-   Go to your G Suite domain's [Admin console](http://admin.google.com/) .
-   Select **Security** from the list of controls.
-   Select **API Controls** then select **Manage Domain Wide Delegation** under **Domain Wide
    Delegation**
-   In the **Client Name** field enter the service account's **Client ID** . You can find your
    service account's client ID in the [Service accounts credentials
    page](https://console.developers.google.com/apis/credentials) or the service account JSON file
    (key named **client_id** ).
-   Click **Add new** to add another API client or use an existing client if you have one. Hover
    over the newly created API client then select **Edit** to add the scopes that you wish to grant
    access to the App. For example, to enable all the scopes required by this app enter:
    -   'https://www.googleapis.com/auth/contacts'
    -   'https://www.googleapis.com/auth/contacts.other.readonly'
    -   'https://www.googleapis.com/auth/directory.readonly'
    -   'https://www.googleapis.com/auth/userinfo.profile'
-   Click **Authorize** .

## Port Information

The app uses HTTP/ HTTPS protocol for communicating with the Google People server. Below are the
default ports used by Splunk SOAR.

|         Service Name | Transport Protocol | Port |
|----------------------|--------------------|------|
|         http         | tcp                | 80   |
|         https        | tcp                | 443  |


### Configuration Variables
The below configuration variables are required for this Connector to operate.  These variables are specified when configuring a Google People asset in SOAR.

VARIABLE | REQUIRED | TYPE | DESCRIPTION
-------- | -------- | ---- | -----------
**key\_json** |  required  | password | Contents of service account JSON file
**login\_email** |  required  | string | Login email

### Supported Actions  
[test connectivity](#action-test-connectivity) - Validate the asset configuration for connectivity using supplied configuration  
[list other contacts](#action-list-other-contacts) - Lists all contacts that are not in a contact group  
[copy contact](#action-copy-contact) - Copy 'Other contact' to 'myContacts' group  
[list directory](#action-list-directory) - Lists all contacts and profiles in the user's domain directory  
[get user profile](#action-get-user-profile) - Provides information about a person given account ID  
[list people](#action-list-people) - Lists authenticated user's contacts  

## action: 'test connectivity'
Validate the asset configuration for connectivity using supplied configuration

Type: **test**  
Read only: **True**

#### Action Parameters
No parameters are required for this action

#### Action Output
No Output  

## action: 'list other contacts'
Lists all contacts that are not in a contact group

Type: **investigate**  
Read only: **True**

This action lists all "Other contacts" which are contacts that are not in another contact group\. These contacts are typically automatically created from interactions\.

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**read\_mask** |  optional  | Comma\-separated list of fields to be returned for each person\. If not provided, default values will be used | string | 
**limit** |  optional  | Number of contacts to include in the response | numeric | 

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.parameter\.read\_mask | string | 
action\_result\.parameter\.limit | numeric | 
action\_result\.data\.\*\.etag | string | 
action\_result\.data\.\*\.names\.\*\.metadata\.source\.id | string | 
action\_result\.data\.\*\.names\.\*\.metadata\.source\.type | string | 
action\_result\.data\.\*\.names\.\*\.metadata\.primary | boolean | 
action\_result\.data\.\*\.names\.\*\.givenName | string | 
action\_result\.data\.\*\.names\.\*\.familyName | string | 
action\_result\.data\.\*\.names\.\*\.displayName | string | 
action\_result\.data\.\*\.names\.\*\.unstructuredName | string | 
action\_result\.data\.\*\.names\.\*\.displayNameLastFirst | string | 
action\_result\.data\.\*\.names\.\*\.middleName | string | 
action\_result\.data\.\*\.resourceName | string |  `googlepeople resource name` 
action\_result\.data\.\*\.emailAddresses\.\*\.value | string |  `email` 
action\_result\.data\.\*\.emailAddresses\.\*\.metadata\.source\.id | string | 
action\_result\.data\.\*\.emailAddresses\.\*\.metadata\.source\.type | string | 
action\_result\.data\.\*\.emailAddresses\.\*\.metadata\.primary | boolean | 
action\_result\.data\.\*\.emailAddresses\.\*\.type | string | 
action\_result\.data\.\*\.emailAddresses\.\*\.formattedType | string | 
action\_result\.data\.\*\.metadata\.sources\.\*\.id | string | 
action\_result\.data\.\*\.metadata\.sources\.\*\.etag | string | 
action\_result\.data\.\*\.metadata\.sources\.\*\.type | string | 
action\_result\.data\.\*\.metadata\.sources\.\*\.updateTime | string | 
action\_result\.data\.\*\.metadata\.objectType | string | 
action\_result\.status | string | 
action\_result\.message | string | 
action\_result\.summary\.total\_otherContacts\_returned | numeric | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric |   

## action: 'copy contact'
Copy 'Other contact' to 'myContacts' group

Type: **generic**  
Read only: **False**

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**resource\_name** |  required  | Resource name of the "Other contact" to copy | string |  `googlepeople resource name` 
**copy\_mask** |  optional  | Comma\-separated list of fields to be copied into the new contact | string | 

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.parameter\.resource\_name | string |  `googlepeople resource name` 
action\_result\.parameter\.copy\_mask | string | 
action\_result\.data\.\*\.etag | string | 
action\_result\.data\.\*\.metadata\.sources\.\*\.id | string | 
action\_result\.data\.\*\.metadata\.sources\.\*\.etag | string | 
action\_result\.data\.\*\.metadata\.sources\.\*\.type | string | 
action\_result\.data\.\*\.metadata\.sources\.\*\.updateTime | string | 
action\_result\.data\.\*\.metadata\.sources\.\*\.profileMetadata\.userTypes | string | 
action\_result\.data\.\*\.metadata\.sources\.\*\.profileMetadata\.objectType | string | 
action\_result\.data\.\*\.metadata\.objectType | string | 
action\_result\.data\.\*\.memberships\.\*\.metadata\.source\.id | string | 
action\_result\.data\.\*\.memberships\.\*\.metadata\.source\.type | string | 
action\_result\.data\.\*\.memberships\.\*\.contactGroupMembership\.contactGroupId | string | 
action\_result\.data\.\*\.memberships\.\*\.contactGroupMembership\.contactGroupResourceName | string | 
action\_result\.data\.\*\.memberships\.\*\.domainMembership\.inViewerDomain | boolean | 
action\_result\.data\.\*\.resourceName | string |  `googlepeople resource name` 
action\_result\.data\.\*\.phoneNumbers\.\*\.value | string | 
action\_result\.data\.\*\.phoneNumbers\.\*\.metadata\.source\.id | string | 
action\_result\.data\.\*\.phoneNumbers\.\*\.metadata\.source\.type | string | 
action\_result\.data\.\*\.phoneNumbers\.\*\.metadata\.primary | boolean | 
action\_result\.data\.\*\.phoneNumbers\.\*\.canonicalForm | string | 
action\_result\.data\.\*\.emailAddresses\.\*\.metadata\.verified | boolean | 
action\_result\.data\.\*\.emailAddresses\.\*\.value | string |  `email` 
action\_result\.data\.\*\.emailAddresses\.\*\.type | string | 
action\_result\.data\.\*\.emailAddresses\.\*\.formattedType | string | 
action\_result\.data\.\*\.emailAddresses\.\*\.metadata\.source\.id | string | 
action\_result\.data\.\*\.emailAddresses\.\*\.metadata\.source\.type | string | 
action\_result\.data\.\*\.emailAddresses\.\*\.metadata\.primary | boolean | 
action\_result\.data\.\*\.names\.\*\.metadata\.source\.id | string | 
action\_result\.data\.\*\.names\.\*\.metadata\.source\.type | string | 
action\_result\.data\.\*\.names\.\*\.metadata\.primary | boolean | 
action\_result\.data\.\*\.names\.\*\.givenName | string | 
action\_result\.data\.\*\.names\.\*\.familyName | string | 
action\_result\.data\.\*\.names\.\*\.displayName | string | 
action\_result\.data\.\*\.names\.\*\.unstructuredName | string | 
action\_result\.data\.\*\.names\.\*\.displayNameLastFirst | string | 
action\_result\.data\.\*\.names\.\*\.middleName | string | 
action\_result\.status | string | 
action\_result\.message | string | 
action\_result\.summary\.total\_contacts\_copied | numeric | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric |   

## action: 'list directory'
Lists all contacts and profiles in the user's domain directory

Type: **investigate**  
Read only: **True**

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**read\_mask** |  optional  | Comma\-separated list of fields to be returned for each person\. If not provided, default values will be used | string | 
**limit** |  optional  | Number of responses to include in the response | numeric | 

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.parameter\.read\_mask | string | 
action\_result\.parameter\.limit | numeric | 
action\_result\.data\.\*\.etag | string | 
action\_result\.data\.\*\.resourceName | string |  `googlepeople resource name` 
action\_result\.data\.\*\.names\.\*\.metadata\.source\.id | string | 
action\_result\.data\.\*\.names\.\*\.metadata\.source\.type | string | 
action\_result\.data\.\*\.names\.\*\.metadata\.primary | boolean | 
action\_result\.data\.\*\.names\.\*\.givenName | string | 
action\_result\.data\.\*\.names\.\*\.familyName | string | 
action\_result\.data\.\*\.names\.\*\.displayName | string | 
action\_result\.data\.\*\.names\.\*\.unstructuredName | string | 
action\_result\.data\.\*\.names\.\*\.displayNameLastFirst | string | 
action\_result\.data\.\*\.names\.\*\.middleName | string | 
action\_result\.data\.\*\.emailAddresses\.\*\.value | string |  `email` 
action\_result\.data\.\*\.emailAddresses\.\*\.metadata\.source\.id | string | 
action\_result\.data\.\*\.emailAddresses\.\*\.metadata\.source\.type | string | 
action\_result\.data\.\*\.emailAddresses\.\*\.metadata\.primary | boolean | 
action\_result\.data\.\*\.emailAddresses\.\*\.metadata\.verified | boolean | 
action\_result\.data\.\*\.emailAddresses\.\*\.type | string | 
action\_result\.data\.\*\.emailAddresses\.\*\.formattedType | string | 
action\_result\.data\.\*\.phoneNumbers\.\*\.type | string | 
action\_result\.data\.\*\.phoneNumbers\.\*\.value | string | 
action\_result\.data\.\*\.phoneNumbers\.\*\.metadata\.source\.id | string | 
action\_result\.data\.\*\.phoneNumbers\.\*\.metadata\.source\.type | string | 
action\_result\.data\.\*\.phoneNumbers\.\*\.metadata\.primary | boolean | 
action\_result\.data\.\*\.phoneNumbers\.\*\.formattedType | string | 
action\_result\.status | string | 
action\_result\.message | string | 
action\_result\.summary\.total\_people\_returned | numeric | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric |   

## action: 'get user profile'
Provides information about a person given account ID

Type: **investigate**  
Read only: **True**

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**resource\_name** |  required  | Resource name of the person to provide info about | string |  `googlepeople resource name` 
**person\_fields** |  optional  | Comma\-separated list of fields to be returned for the person | string | 

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.parameter\.resource\_name | string |  `googlepeople resource name` 
action\_result\.parameter\.person\_fields | string | 
action\_result\.data\.\*\.metadata\.sources\.\*\.id | string | 
action\_result\.data\.\*\.metadata\.sources\.\*\.etag | string | 
action\_result\.data\.\*\.metadata\.sources\.\*\.type | string | 
action\_result\.data\.\*\.metadata\.sources\.\*\.updateTime | string | 
action\_result\.data\.\*\.metadata\.objectType | string | 
action\_result\.data\.\*\.etag | string | 
action\_result\.data\.\*\.names\.\*\.middleName | string | 
action\_result\.data\.\*\.names\.\*\.metadata\.source\.id | string | 
action\_result\.data\.\*\.names\.\*\.metadata\.source\.type | string | 
action\_result\.data\.\*\.names\.\*\.metadata\.primary | boolean | 
action\_result\.data\.\*\.names\.\*\.givenName | string | 
action\_result\.data\.\*\.names\.\*\.familyName | string | 
action\_result\.data\.\*\.names\.\*\.displayName | string | 
action\_result\.data\.\*\.names\.\*\.unstructuredName | string | 
action\_result\.data\.\*\.names\.\*\.displayNameLastFirst | string | 
action\_result\.data\.\*\.names\.\*\.honorificSuffix | string | 
action\_result\.data\.\*\.resourceName | string |  `googlepeople resource name` 
action\_result\.data\.\*\.emailAddresses\.\*\.type | string | 
action\_result\.data\.\*\.emailAddresses\.\*\.formattedType | string | 
action\_result\.data\.\*\.emailAddresses\.\*\.value | string |  `email` 
action\_result\.data\.\*\.emailAddresses\.\*\.metadata\.source\.id | string | 
action\_result\.data\.\*\.emailAddresses\.\*\.metadata\.source\.type | string | 
action\_result\.data\.\*\.emailAddresses\.\*\.metadata\.primary | boolean | 
action\_result\.data\.\*\.emailAddresses\.\*\.metadata\.verified | boolean | 
action\_result\.status | string | 
action\_result\.message | string | 
action\_result\.summary\.resource\_id\_returned | string | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric |   

## action: 'list people'
Lists authenticated user's contacts

Type: **investigate**  
Read only: **True**

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**person\_fields** |  optional  | Comma\-separated list of fields to be returned for each person\. If not provided, default values will be used | string | 
**limit** |  optional  | Number of connections to include in the response | numeric | 

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.parameter\.person\_fields | string | 
action\_result\.parameter\.limit | numeric | 
action\_result\.data\.\*\.names\.\*\.metadata\.source\.id | string | 
action\_result\.data\.\*\.names\.\*\.metadata\.source\.type | string | 
action\_result\.data\.\*\.names\.\*\.metadata\.primary | boolean | 
action\_result\.data\.\*\.names\.\*\.givenName | string | 
action\_result\.data\.\*\.names\.\*\.familyName | string | 
action\_result\.data\.\*\.names\.\*\.displayName | string | 
action\_result\.data\.\*\.names\.\*\.unstructuredName | string | 
action\_result\.data\.\*\.names\.\*\.displayNameLastFirst | string | 
action\_result\.data\.\*\.names\.\*\.middleName | string | 
action\_result\.data\.\*\.etag | string | 
action\_result\.data\.\*\.resourceName | string |  `googlepeople resource name` 
action\_result\.data\.\*\.emailAddresses\.\*\.type | string | 
action\_result\.data\.\*\.emailAddresses\.\*\.formattedType | string | 
action\_result\.data\.\*\.emailAddresses\.\*\.value | string |  `email` 
action\_result\.data\.\*\.emailAddresses\.\*\.metadata\.source\.id | string | 
action\_result\.data\.\*\.emailAddresses\.\*\.metadata\.source\.type | string | 
action\_result\.data\.\*\.emailAddresses\.\*\.metadata\.primary | boolean | 
action\_result\.data\.\*\.metadata\.sources\.\*\.id | string | 
action\_result\.data\.\*\.metadata\.sources\.\*\.etag | string | 
action\_result\.data\.\*\.metadata\.sources\.\*\.type | string | 
action\_result\.data\.\*\.metadata\.sources\.\*\.updateTime | string | 
action\_result\.data\.\*\.metadata\.objectType | string | 
action\_result\.data\.\*\.birthdays\.\*\.date\.day | numeric | 
action\_result\.data\.\*\.birthdays\.\*\.date\.year | numeric | 
action\_result\.data\.\*\.birthdays\.\*\.date\.month | numeric | 
action\_result\.data\.\*\.birthdays\.\*\.text | string | 
action\_result\.data\.\*\.birthdays\.\*\.metadata\.source\.id | string | 
action\_result\.data\.\*\.birthdays\.\*\.metadata\.source\.type | string | 
action\_result\.data\.\*\.birthdays\.\*\.metadata\.primary | boolean | 
action\_result\.status | string | 
action\_result\.message | string | 
action\_result\.summary\.total\_people\_returned | numeric | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric | 