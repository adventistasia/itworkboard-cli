import msal

from workboard_cli.config import load_config


def get_token(tenant_id=None, client_id=None):
    if not tenant_id or not client_id:
        cfg = load_config()
        tenant_id = cfg["tenant_id"]
        client_id = cfg["client_id"]

    authority = f"https://login.microsoftonline.com/{tenant_id}"
    app = msal.PublicClientApplication(client_id, authority=authority)

    scopes = ["https://graph.microsoft.com/Sites.Read.All"]
    flow = app.initiate_device_flow(scopes=scopes)
    if "user_code" not in flow:
        raise RuntimeError(
            f"Device flow failed: {flow.get('error_description', flow)}"
        )

    print(f"Open: {flow['verification_uri']}")
    print(f"Code: {flow['user_code']}")

    result = app.acquire_token_by_device_flow(flow)
    if "access_token" not in result:
        raise RuntimeError(
            f"Auth failed: {result.get('error_description', result)}"
        )

    return result["access_token"]
