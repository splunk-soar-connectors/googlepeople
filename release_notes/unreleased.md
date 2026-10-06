**Unreleased**
* Convert all five Google People actions and test connectivity to the Splunk SOAR SDK.
* Preserve app version 1.1.11, app ID, action names and identifiers, delegated service-account authentication, per-action scopes, parameters, summaries, raw API result fields, CEF metadata, table columns and custom views.
* Require Splunk SOAR 7.0.0 or later (previously 6.3.0), following the SDK minimum.
* Support Python 3.13; remove Python 3.9 support. Python 3.14 is not enabled in this conversion.
* Replace the legacy connector module with the SDK entry point `src.app:app`; retain the app ID and action identifiers for existing assets and playbooks. Retain package name `phantom_googlepeople`.
* Add unit regression coverage for complete serialized results, missing fields, explicit null summaries, undeclared API fields, authentication, validation and pagination safeguards.
* Reject blank or whitespace-only resource names in get user profile before creating the Google client, restoring legacy required-parameter validation.
* Omit the configured login email from connectivity progress messages.
* Add a `make_request` action for Google People API v1 endpoints, restricted to the People API host and Contacts scope.
