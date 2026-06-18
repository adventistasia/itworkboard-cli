# Azure AD App Registration Checklist

Use this to set up the app registration needed before discovery can run.

## Target

- SharePoint site: `https://southernasiapacific.sharepoint.com/sites/ITWorkboard`
- Primary list: `WorkBoard`

---

## 1. Create the app registration

- [x] Go to [Azure Portal](https://portal.azure.com) → **Microsoft Entra ID** → **App registrations** → **New registration**
- [x] Name: `WorkBoard CLI`
- [x] Supported account types: **Accounts in this organizational directory only** (single tenant)
- [x] Redirect URI: leave blank
- [x] Click **Register**
- [x] **Copy** the following from the Overview page:

| Field | Value (paste here) |
|-------|-------------------|
| Application (client) ID | `<paste-client-id>` |
| Directory (tenant) ID | `<paste-tenant-id>` |

## 2. Enable device code flow

- [x] Left nav → **Authentication**
- [x] Under **Advanced settings** → **Allow public client flows**, toggle **Yes**
- [x] Click **Save**

## 3. Add Graph API permission

- [x] Left nav → **API permissions** → **Add a permission**
- [x] Choose **Microsoft Graph** → **Delegated permissions**
- [x] Search for and check **`Sites.Read.All`**
- [x] Click **Add permissions**
- [x] **Grant admin consent** (click the button, confirm) — otherwise the first login will prompt for consent

## 4. Verify the app

- [x] Go back to **Overview**
- [x] Confirm **Application ID** and **Directory ID** are noted somewhere safe
- [x] Confirm **"Allow public client flows"** shows **Yes**
- [x] Confirm **API permissions** shows **`Sites.Read.All`** with status **Granted for ...**

## 5. Run discovery

- [ ] Open a terminal in this repo
- [ ] Run:

```powershell
$env:WORKBOARD_TENANT_ID = "<paste-tenant-id>"
$env:WORKBOARD_CLIENT_ID = "<paste-client-id>"
python -m workboard_cli.discovery_spike
```

- [ ] A URL and code will print. Open the URL in a browser, enter the code, sign in with your work account
- [ ] Verify `discovery/` directory has output files:

```
discovery/site.json
discovery/lists.json
discovery/workboard_schema.json
discovery/workboard_sample_items.json
discovery/permission_report.md
```

## 6. Share with the agent

- [x] Share the **Tenant ID** and **Client ID** with the agent (not the secret — no secret needed for device code flow)

---

## Troubleshooting

| Problem | Likely cause | Fix |
|---------|-------------|-----|
| `device_flow_failed` | Public client flow not enabled | Go back to step 2 |
| `permission_denied` on site resolution | `Sites.Read.All` not granted, or admin consent missing | Go back to step 3 |
| `permission_denied` on lists/items | User doesn't have access to the SharePoint site | Request site access from an admin |
| `not_found` on site resolution | Wrong tenant or site URL | Verify tenant ID and target site URL It doesn't freeze me Apple. |
