# Admin permissions

## Required Azure AD app registration

Create an app registration in the Azure portal with:

- **Name**: `IT WorkBoard CLI`
- **Supported account types**: `Accounts in this organizational directory only`
- **Authentication**: `Mobile and desktop applications` → `https://login.microsoftonline.com/common/oauth2/native/client`
- **API permissions**: Microsoft Graph → Delegated permissions → `Sites.Read.All`

## Why Sites.Read.All?

`Sites.Read.All` is the minimum scope needed to read SharePoint lists and items across a known site. The CLI never requests write scopes.

## Checklist for admin

- [ ] Azure AD app registration created
- [ ] `Sites.Read.All` delegated permission granted
- [ ] Admin consent granted (if required by tenant policy)
- [ ] Tenant ID and Client ID shared with the team

## Security notes

- The CLI uses device code flow — no client secret needed
- No app-only (client credentials) flow in v1
- Access is on behalf of the authenticated user
- Tokens are cached in memory only
