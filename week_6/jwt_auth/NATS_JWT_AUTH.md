# NATS JWT Decentralized Authentication — Architecture & Sequence Reference

Operator / Account / User trust chain, connection handshake, and permission enforcement.

`Ed25519 / NKeys` · `Decentralized trust` · `Challenge-response` · `Zero password storage`

---

## 1. Trust hierarchy

Every identity in NATS decentralized auth is an NKey pair (an Ed25519 keypair with a typed prefix). The **Operator** signs the **Account** JWT; the **Account** signs the **User** JWT. The server only ever needs to trust the Operator's public key — everything below it is verified cryptographically, not looked up in a database.

```
Operator
  Seed:   SO...
  Public: OA...
   │
   │  signs
   ▼
Account
  Seed:   SA...
  Public: AA...
   │
   │  signs
   ▼
User
  Seed:   SU...
  Public: UA...
```

**NATS server** trusts only the Operator's public key.

Trust flows downward through signatures; verification flows upward through the same chain.

### Why the Operator exists

- **One thing to configure, not many.** Without an Operator layer, the server would need to know every Account directly. With an Operator, the server config holds exactly one public key — it never changes as accounts are added, removed, or rotated.
- **It's the delegation boundary.** Signing an Account JWT is the Operator saying "this Account is legitimate." Once signed, the Account creates and signs as many Users as it wants with zero further involvement from the Operator or the server. This is what makes the system decentralized.
- **It enables multi-tenancy.** Each team or tenant gets its own Account, cryptographically isolated from the others — the server enforces subject-space isolation between accounts automatically.
- **It supports multiple environments/organizations on one deployment.** A server can even trust more than one Operator, each anchoring its own independent Account/User tree (e.g. one per customer in a SaaS setup).
- **It replaces "the server as source of truth."** Authority moves from a live user database to a signing chain; the server's job shrinks to "verify signatures chain back to a key I trust."

---

## 2. Connection begins

```
Client (Order Service)  ──── TCP connection ────▶  NATS Server
                                                     (accepts connection)
```

The client opens a raw TCP connection to a NATS server. No credentials have been exchanged yet — this is just the transport handshake.

---

## 3. INFO message

Immediately after accepting the connection, the server sends an `INFO` message containing a fresh random nonce:

```json
INFO
{
  "nonce": "a92K..."
}
```

- **Random nonce** — generated per connection, never reused.
- **Fresh every connection** — a new value each time a client connects.
- **Prevents replay attacks** — a captured signature from a previous connection can't be replayed, because it was signed over a nonce that will never appear again.

---

## 4. Client cryptographic operation

```
Nonce  +  User private seed
                │
                ▼
        Ed25519 signature
```

The client signs the received nonce with its User private seed, producing an Ed25519 signature.

**Local cryptographic operation — the private seed never leaves the client.** Only the resulting signature is transmitted; the seed itself is never sent over the wire, never seen by the server, and never stored server-side.

---

## 5. CONNECT message

The client responds with a `CONNECT` message:

```json
CONNECT
{
  "jwt":  "...",
  "nkey": "UA...",
  "sig":  "..."
}
```

| Field | Meaning |
|---|---|
| `jwt` | Identity — the signed User JWT issued by the Account |
| `nkey` | The User's public key (`UA...`) |
| `sig` | Proof of private key ownership — the Ed25519 signature over the server's nonce |

---

## 6. Server verification pipeline

The server runs seven checks in strict sequence. Any failure rejects the connection immediately — nothing downstream executes.

**Step 1 — Decode JWT → extract claims**

**Step 2 — Read `iss` → find Account**
The `iss` (issuer) claim on the User JWT identifies which Account signed it.

**Step 3 — Verify User JWT signature, using Account public key**
✓ valid / ✗ reject

**Step 4 — Verify Account JWT, using Operator public key**
✓ trusted / ✗ reject

**Step 5 — Validate JWT claims**
Expiration · Not Before · Issued At — invalid → reject.

**Step 6 — Compare JWT subject with CONNECT nkey**
JWT subject (`UA...`) must match the `nkey` field sent in CONNECT (`UA...`) — mismatch → reject.
This stops someone from presenting a valid JWT for one identity while proving ownership of a different key.

**Step 7 — Verify nonce signature**
Inputs: nonce, sig, user public key → Ed25519 verification. Invalid → reject.

→ **Authentication successful**

---

## 7. Permission loading

Publish and subscribe permissions live inside the verified User JWT itself.

```json
User JWT
{
  "publish":   "orders.*",
  "subscribe": "inventory.*"
}
```

| Action | Result |
|---|---|
| `publish orders.created` | ✓ allowed |
| `publish payments.created` | ✗ permission denied |

**No database lookup** — permissions are read directly from the verified JWT, not queried from a permissions table.

---

## 8. Complete authentication timeline

```
Client                                   Server
  │                                         │
  │──────────── TCP connect ──────────────▶│
  │                                         │
  │◀──────────── INFO + nonce ─────────────│
  │                                         │
  │  sign nonce                            │
  │  (local, Ed25519)                      │
  │                                         │
  │─────── CONNECT (jwt, nkey, sig) ──────▶│
  │                                         │  verify User JWT
  │                                         │  verify Account JWT
  │                                         │  verify signature
  │                                         │  load permissions
  │                                         │  → authenticated
  │                                         │
  │◀───────────────── +OK ─────────────────│
```

---

## 9. Security benefits

| Traditional authentication | JWT + NKeys |
|---|---|
| Server stores all users | Server stores only the trusted Operator |
| Passwords travel over the authentication flow | No password ever transmitted or verified |
| Difficult to scale user management | Accounts manage their own users independently |
| Centralized identity store | Decentralized, cryptographic trust chain |
| Static credential presented each time | Challenge-response signature, replay resistant |

---

## 10. Final summary

```
Operator
   │  signs
   ▼
Account
   │  signs
   ▼
User JWT
   │
   ▼
Client connects
   │
   ▼
Server sends nonce
   │
   ▼
Client signs nonce
   │
   ▼
Server verifies:
  ✓ operator   ✓ account   ✓ user
  ✓ jwt claims ✓ signature
   │
   ▼
Authenticated
```

---

## Additional details worth knowing

### Revocation
JWTs are bearer-style credentials with an expiry, but a server also needs a way to cut off access *before* expiry (e.g. an employee leaves, a key leaks). NATS supports this at two levels:
- **Account-level revocation list** — an Account JWT can carry a list of revoked User public keys with a timestamp; any User JWT issued before that timestamp for that key is rejected even if it hasn't expired.
- **Operator-level revocation** — the same mechanism exists one level up, letting an Operator revoke an entire Account.

Without this, a compromised private seed can only be neutralized by waiting out the JWT's expiration.

### Key rotation and signing keys vs identity keys
Operators and Accounts can have additional **signing keys** distinct from their main identity key. Day-to-day JWT issuance uses a signing key; the main identity keypair stays offline in cold storage. If a signing key is compromised, it can be revoked and rotated without changing the Operator's or Account's public identity — which would otherwise require reconfiguring every server that trusts it.

### The System Account
Most deployments define a special **System Account**. It receives internal server events (connect/disconnect, auth failures, slow consumers) on reserved subjects, which is how you monitor authentication activity — e.g. alerting on repeated Step 3/4/7 rejections — without granting broad visibility to regular Accounts.

### Account isolation (subject namespace)
Each Account gets its own isolated subject space by default. Two Accounts can both publish to `orders.created` without collision, because subjects are scoped per Account unless explicitly shared. Cross-account communication requires an explicit **export/import** configuration on the Account JWTs — the Account owning a subject exports it, and another Account must import it to see it. This is a separate mechanism from the publish/subscribe permissions in Section 7, which govern what a *User within* an Account can do.

### How the server actually resolves an Account JWT (Step 2, in practice)
"Find Account" in Step 2 isn't a network call to a central server — it's a lookup against one of three resolver types configured on the NATS server itself:
- **Memory resolver** — Account JWTs are embedded directly in the server config file (small/static deployments).
- **URL resolver** — the server fetches Account JWTs from an HTTP(S) endpoint on demand.
- **Full/NATS-based resolver (nsc + `nats-server` account resolver)** — Account JWTs are pushed into the server via a NATS-native protocol and cached locally, which is what NGS (Synadia's global network) and most production deployments use.

In all three cases, the server still cryptographically verifies the fetched Account JWT against the Operator key in Step 4 — the resolver just answers "where do I find the JWT," not "should I trust it."

### JWT claim structure (what's actually inside `jwt`)
The `jwt` in Section 5 isn't opaque — it follows the standard JWT format (`header.payload.signature`), but the payload's claims are NATS-specific. Beyond `iss` (issuer, used in Step 2) and `sub` (subject, used in Step 6), a User JWT payload typically also carries:
- `nats.pub` / `nats.sub` — the permission patterns from Section 7
- `nats.limits` — connection-level limits (max subscriptions, max payload size, max data/msgs per second)
- `nats.resp` — allowed response permissions, for request-reply patterns
- `exp`, `nbf`, `iat` — the timestamp claims checked in Step 5

