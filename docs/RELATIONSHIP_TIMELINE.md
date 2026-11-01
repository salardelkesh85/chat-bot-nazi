# Relationship Timeline

Each companion has an independent timeline of owner-curated story events.

## Event fields
- title: required, up to 120 characters
- description: optional, up to 2,000 characters
- event_type: milestone, memory, first_time, shared_interest, or custom
- occurred_at: optional event date; defaults to current UTC time

## API
- GET /api/companions/{companion_id}/timeline
- POST /api/companions/{companion_id}/timeline
- DELETE /api/companions/{companion_id}/timeline/{event_id}

Events are explicitly added by the owner. They are not inferred or stored automatically from chat. This keeps personal story details under the owner's control.

The data is stored in the local SQLite database and is deleted with its companion.
