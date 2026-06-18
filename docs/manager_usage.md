# Manager usage

## Install and authenticate

```bash
pip install .
workboard auth login
```

## Daily summary

```bash
workboard summary manager
```

Returns a markdown report with:
- Total items, overdue count, blocked count
- Items grouped by stage category
- Items grouped by delivery owner

## Common queries

```bash
# What's overdue?
workboard query overdue

# What's blocked?
workboard query blocked

# Who owns what?
workboard query by-owner --owner "Jane"

# What changed recently?
workboard query recently-updated --days 7
```

## Export filter details

```bash
workboard query open --format json
```

The JSON output includes `source` metadata (site URL, list name, retrieval timestamp) so results are traceable back to SharePoint.
