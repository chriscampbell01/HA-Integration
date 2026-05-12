# HA-Integration

Minimal HTTP API for Home Assistant integrations.

## Run the API

```bash
python ha_api.py
```

Optional environment variables:

- `HOST` (default: `127.0.0.1`)
- `PORT` (default: `8080`)
- `HA_API_TOKEN` (optional bearer token required for `POST /api/v1/events`)
- `HA_API_LOG_REQUESTS` (`true`/`1`/`yes` enables HTTP request logs)

## Endpoints

- `GET /health` → basic health check
- `GET /api/v1/state` → integration status payload
- `POST /api/v1/events` → accept event payload from Home Assistant

Example event payload:

```json
{
  "event": "light_toggle",
  "data": {
    "entity_id": "light.living_room"
  }
}
```

## Home Assistant example (`rest_command`)

```yaml
rest_command:
  ha_integration_event:
    url: "http://YOUR_API_HOST:8080/api/v1/events"
    method: POST
    headers:
      Authorization: "Bearer YOUR_HA_API_TOKEN"
      Content-Type: "application/json"
    payload: >
      {
        "event": "{{ event_name }}",
        "data": {{ event_data | tojson }}
      }
```
