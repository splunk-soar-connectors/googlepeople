# Google People SDK conversion

The conversion uses Splunk SOAR SDK 6.1.2 and keeps app version 1.1.11.
The baseline is commit `3aa97eabea3cc60fb2ced44c3cfa5ecb0b6f5943`.
The original manifest is retained as `tests/fixtures/legacy_manifest.json`.

## Preserved behavior

All five actions and connectivity testing retain their action names and identifiers:
`list_other_contacts`, `copy_contact`, `list_directory`, `get_user_profile`,
`list_people` and `test_connectivity`.
The app ID remains `cfeed12d-b40f-477a-b9f9-59c37d12ebfe`, and package name remains
`phantom_googlepeople`.

Google's service-account credentials, domain-wide delegation through `login_email`,
action-specific scopes and discovery client are retained. Google service-account
JWT authentication is not interchangeable with a client-credentials OAuth flow.
Google's credential library continues to refresh access tokens. No interactive
OAuth callback or state migration is needed because the legacy app did not persist
authentication tokens or ingestion checkpoints.
Runtime Google imports stay inside helper functions because manifest generation
loads app modules in the packaging tool's environment, which can lack app-specific
dependencies.

Masks retain their defaults and comma-separated validation. Limits retain positive
integer validation, page size 1000, truncation, the 100-page and 10000-item limits,
repeated-token protection and the three-consecutive-empty-page guard.
The legacy copy-contact resource check intentionally remains a substring check.
Blank or whitespace-only profile resource names are rejected before client creation,
restoring the legacy platform's required-parameter validation. Connectivity progress
messages omit the configured login email.

Every API result model derives from `PermissiveActionOutput`. Declared fields
retain the SOAR metadata, while serialization keeps the original response,
including undeclared fields, nested arrays, explicit nulls and missing fields.
Nested fields are declared with `OutputField()` defaults rather than Optional
annotations, since the SDK inserts nulls for omitted Optional fields.
The legacy API handlers inserted no data defaults. The profile summary explicitly
returns `resource_id_returned: null` when `resourceName` is absent.
The other-contacts summary retains the alias `total_otherContacts_returned`.
`LegacyParams` preserves the caller's parameter keys in the result echo while
allowing omitted masks to use the API defaults.

The table column names, datapaths and numeric order match the legacy manifest.
`PersonOutput._to_json_schema` restores their explicit order because the SDK's
recursive field traversal cannot express the profile table's interleaved name and
email metadata columns through declaration order alone. Regression tests cover
this override against the pinned SDK.
The copy-contact and directory custom views retain the `googlepeople` wrapper and
column order. Their templates use Jinja, a numeric container ID and HTML-escaped
JSON values for context menus.

## Make request action

The `make_request` action adds access to Google People API v1 endpoints that are
not exposed as dedicated actions, including contact creation, contact groups and
contact search. It retains service-account delegation and uses the existing
`https://www.googleapis.com/auth/contacts` scope. The domain-wide delegation
configuration must authorize this scope; write operations additionally require
the corresponding Google API permissions.

Requests are limited to relative `/v1/` paths on `https://people.googleapis.com`.
Absolute URLs, fragments, path traversal and caller-supplied authorization/host
headers are rejected. Query values are passed as structured parameters; JSON
bodies are parsed before sending. The action applies a 30-second timeout when
none is provided, verifies TLS by default, and returns the HTTP status and body,
including non-2xx responses, for playbook handling.

## Validation

The golden result fixture was captured by executing the original action handlers
with mocked Google responses and a local ActionResult shim. The SDK tests compare
complete data, summary, message, status and parameter echo through the SDK result
adapter, along with scopes and API request arguments. Cases cover full responses,
unknown nested fields, missing fields, explicit nulls and multiple records.
Additional tests cover authentication failures, invalid configuration, masks,
limits, pagination, CEF metadata, table order and custom view rendering/escaping.

Run unit tests with `.venv/bin/python -m pytest tests -q` or `soarapps test unit`.
Run repository validation with
`/Users/atkm/.local/bin/pre-commit run --all-files`.
Build with `soarapps package build -o googlepeople-1.1.11-sdk.tgz`.

The version 1.1.11 SDK package was installed on the dedicated SOAR 8.7.0.170 test
instance. On October 5, 2026, the Google People app-tests run completed with
101 passed, 1 skipped and 4 deselected in 486.24 seconds, with no failures or
errors. Backend connectivity and all 100 action tests passed, covering all five
actions with delegated service-account credentials.

The harness skips UI connectivity for Google People. Bad-asset cases were
deselected because their separate local asset still contains credential
placeholders. ChromeDriver was updated to match the installed Chrome for browser
fixture setup. Actual SOAR widget presentation and instance log checks remain
pending; offline template and manifest tests cover rendering and metadata.
No instance credentials or vendor secrets are stored in this repository.
