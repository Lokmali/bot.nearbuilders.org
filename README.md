# bot.nearbuilders.org

## Telegram Bot Builder Nomination Guide

### 1. Create an API Key

A logged-in user (e.g., `nathan.near`) creates an API key through the UI or server-side:

**Via UI:** Settings → API Keys → Create Key

**Via API (server-side):**

```bash
# First, get a session cookie by signing in via NEAR SIWN
# Then create an API key:
curl -X POST https://nearbuilders.org/api/auth/api-key/create \
  -H "Content-Type: application/json" \
  -H "Cookie: <session-cookie>" \
  -d '{
    "name": "nearbuildersbot",
    "configId": "user-keys"
  }'
```

Response includes the full key (prefixed, e.g., `nb_k_live_xxxxx...`). **Save this** — it only appears once.

If you need scoped permissions (not required for `propose`, any key works), create server-side:

```bash
curl -X POST https://nearbuilders.org/api/auth/api-key/create \
  -H "Content-Type: application/json" \
  -H "Cookie: <session-cookie>" \
  -d '{
    "name": "nearbuildersbot",
    "configId": "user-keys",
    "permissions": {
      "proposals": ["create"]
    }
  }'
```

**Permissions note:** The `propose` endpoint accepts ANY valid API key — no specific permissions are checked. The `requireAuthOrApiKey` middleware only verifies the key exists and is valid. You can optionally set permissions for future use or auditing, but they're not enforced on `propose` today.

### 2. Nominate a Builder via Telegram Bot

The bot calls the API with the API key:

```bash
curl -X POST https://nearbuilders.org/api/rpc/proposals \
  -H "Content-Type: application/json" \
  -H "x-api-key: nb_k_live_xxxxx..." \
  -d '{
    "pluginId": "builders",
    "entityId": "alice.near",
    "payload": {
      "name": "Alice",
      "bio": "Smart contract developer on NEAR",
      "skills": ["Rust", "Smart Contracts", "NEAR"],
      "location": "Remote"
    },
    "source": "telegram",
    "metadata": {
      "nominatedBy": "telegram:123456789",
      "telegramChatId": -1001234567890
    }
  }'
```

**Key fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `pluginId` | string | Yes | Always `"builders"` |
| `entityId` | string | Yes | NEAR account ID (e.g., `"alice.near"`) or platform-scoped ID (e.g., `"telegram:123456789"`) if NEAR account not yet linked |
| `payload` | object | Yes | Builder data: `name`, `bio`, `skills` (array), `location`, `links` (object), `userId` |
| `source` | string | No | Origin label, e.g., `"telegram"` |
| `metadata` | object | No | Arbitrary JSON — use for tracking (e.g., `{"nominatedBy": "telegram:123456789"}`) |
| `idempotencyKey` | string | No | Dedup key — use to prevent double submissions from the same nomination |

**For users without NEAR accounts yet:** Use `entityId: "telegram:<user_id>"`. When the admin approves, they should update the `entityId` to the actual NEAR account (or the Telegram bot can resolve it later). The `createBuilder` callback will receive `nearAccount: "telegram:123456789"` which will need NEAR account resolution during or before approval.

### 3. What Happens Next

1. **Proposal created** with `reviewStatus: "pending"`, `createdBy: <api-key-owner-userId>`, `source: "telegram"`
2. **Admin reviews** at `/dashboard` — sees the proposal with name, bio, skills, location
3. **Admin approves** → `createCallbacks.builders` fires → builder record created in the database
4. **Builder appears** on `/builders` listing and `/builders/:account` profile page

**If NEAR account not yet linked** (`entityId` is `telegram:123456789`):
- The admin dashboard will show `telegram:123456789` as the entity ID
- Admin should coordinate NEAR account linking before approval, or the Telegram bot should gather the NEAR account during a conversation with the nominated user first

### 4. Idempotency

To prevent duplicate nominations from the same Telegram message:

```bash
curl -X POST https://nearbuilders.org/api/rpc/proposals \
  -H "Content-Type: application/json" \
  -H "x-api-key: nb_k_live_xxxxx..." \
  -d '{
    "pluginId": "builders",
    "entityId": "alice.near",
    "payload": { ... },
    "source": "telegram",
    "metadata": { "nominatedBy": "telegram:123456789" },
    "idempotencyKey": "tg-nom-123456789-alice.near"
  }'
```

If the same `(pluginId, idempotencyKey)` is submitted again, the existing proposal is returned without creating a duplicate.

### 5. Checking Proposal Status

```bash
curl -G https://nearbuilders.org/api/rpc/proposals \
  -H "x-api-key: nb_k_live_xxxxx..." \
  --data-urlencode "pluginId=builders" \
  --data-urlencode "entityId=alice.near"
```

Returns proposals with `reviewStatus`: `"pending"`, `"approved"`, `"rejected"`, or `"removed"`.
