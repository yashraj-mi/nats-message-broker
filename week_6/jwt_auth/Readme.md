# Decentralized JWT Authentication for NATS

This project implements **decentralized JWT authentication** for a NATS server using the
**Operator → Account → User** trust model, `nsc` (the NATS security CLI), and Python clients
via `nats-py`.

This README documents *everything* that was done, *why* it was done, and exactly how to
reproduce, run, and verify it — so you (or anyone else) can rebuild this from scratch just by
following it top to bottom.

---

## 1. Core Concept — How Decentralized JWT Auth Works

Traditional NATS auth (username/password, static tokens) needs a central place to check
credentials. Decentralized JWT auth instead uses a **cryptographic trust chain**:

```
Operator (root of trust)
   └── signs → Account JWTs (isolated tenants/namespaces)
                  └── signs → User JWTs (individual client identities)
```

- Every level (**Operator**, **Account**, **User**) has its own **nkey** — an Ed25519
  keypair (like SSH keys, but NATS-specific).
- A JWT at each level is **signed by the private key of the level above it**.
- The NATS server only needs to know the **Operator's public key**. From that single trust
  anchor, it can cryptographically verify the *entire* chain — Account JWTs, User JWTs,
  permissions — without ever calling out to a database or auth server at connection time.
- This is what makes it "**decentralized**": trust is verified locally via signatures, not
  looked up centrally.

**Why Accounts matter:** each Account is a fully isolated subject space (multi-tenancy).
Two accounts can both publish/subscribe to `app.>` and never see each other's messages,
unless one explicitly **exports** a subject and the other **imports** it.

---

## 2. Prerequisites

| Tool | Purpose | Install |
|---|---|---|
| `nsc` | CLI to create/manage operators, accounts, users, JWTs, nkeys | `curl -L https://raw.githubusercontent.com/nats-io/nsc/main/install.sh \| sh` |
| `nats-server` | The actual NATS server binary | Download from [nats-server releases](https://github.com/nats-io/nats-server/releases) |
| `nats` CLI | Command-line pub/sub testing client | Download from [natscli releases](https://github.com/nats-io/natscli/releases) |
| `nats-py` | Python client library | `pip install nats-py` |

After installing `nsc`, make sure its bin directory is on your `PATH`:

```bash
echo 'export PATH=$HOME/.local/bin:$PATH' >> ~/.bashrc
source ~/.bashrc
nsc --version
nats-server -v
nats --version
```

---

## 3. Project Structure

```
jwt-auth/
│
├── operator/               # Exported Operator JWT (root of trust)
│   └── operator.jwt
│
├── accounts/                # Exported Account JWTs (per-tenant backup copies)
│   ├── company-a/
│   │   └── company-a.jwt
│   └── company-b/
│       └── company-b.jwt
│
├── users/                    # Exported User JWTs (per-user backup copies)
│   ├── publisher/
│   ├── subscriber/
│   └── notification/
│
├── creds/                    # .creds files - JWT + private nkey seed, used by clients
│   ├── publisher.creds       # NEVER commit these - private key material
│   ├── subscriber.creds
│   └── notification.creds
│
├── configs/
│   ├── server.conf           # nats-server config (operator + resolver)
│   └── jwt-store/            # Server-managed resolver directory (auto-populated by nsc push)
│
├── publisher.py               # company-a: publish-only client
├── subscriber.py               # company-a: subscribe-only client (app.order.> only)
├── notification.py             # company-b: subscribe-only client (app.events.> only, cross-account import)
│
└── README.md
```

**Note:** `nsc` also keeps its own internal store (the actual source of truth for all keys and
JWTs) at `~/.local/share/nats/nsc` by default. The files inside our project folder are
*exported copies* for reference, backup, and for the server/clients to actually use at runtime.

---

## 4. Step-by-Step Implementation

### Step 1 — Create the Operator (root of trust)

```bash
nsc add operator --name MyOperator --generate-signing-key --sys
```

| Flag | What it does |
|---|---|
| `add operator --name MyOperator` | Creates the Operator identity: an nkey pair (`O...` public key) and a self-signed Operator JWT. |
| `--generate-signing-key` | Generates a separate **signing key** for the operator. Best practice: sign Account JWTs with this key, not the root operator key, so the root key can stay offline/untouched and the signing key can be rotated if compromised. |
| `--sys` | Auto-creates the built-in `SYS` (system) account, needed for server administration and for `nsc push` to work. |

Export it so the server config can reference it:

```bash
nsc describe operator --raw > operator/operator.jwt
```

> ⚠️ **Re-run this export any time you `nsc edit operator`** — the JWT changes and the file on
> disk becomes stale otherwise.

Verify:

```bash
nsc describe operator
```

---

### Step 2 — Create the Accounts (tenants)

Each Account is an isolated namespace. We created two: `company-a` and `company-b`.

```bash
nsc add account --name company-a
nsc edit account company-a --sk generate

nsc add account --name company-b
nsc edit account company-b --sk generate
```

- `add account --name ...` — creates the account nkey pair (`A...` public key) and an Account
  JWT signed by the operator's signing key.
- `edit account --sk generate` — adds a **signing key** to the account, used to sign this
  account's User JWTs (same rotation-safety reasoning as the operator's signing key).

Export for backup:

```bash
nsc describe account company-a --raw > accounts/company-a/company-a.jwt
nsc describe account company-b --raw > accounts/company-b/company-b.jwt
```

Verify:

```bash
nsc list accounts
nsc describe account company-a
```

---

### Step 3 — Create the Users

Account placement:
- `company-a` → `publisher`, `subscriber` (talk to each other, same tenant)
- `company-b` → `notification` (separate tenant, receives cross-account events)

```bash
nsc add user --account company-a --name publisher
nsc add user --account company-a --name subscriber
nsc add user --account company-b --name notification
```

Each command creates a user nkey pair (`U...` public key) and a User JWT signed by that
account's signing key.

Export for backup:

```bash
nsc describe user --account company-a publisher     --raw > users/publisher/publisher.jwt
nsc describe user --account company-a subscriber     --raw > users/subscriber/subscriber.jwt
nsc describe user --account company-b notification   --raw > users/notification/notification.jwt
```

Verify:

```bash
nsc list users --account company-a
nsc list users --account company-b
```

---

### Step 4 — Generate `.creds` files (what clients actually connect with)

A `.jwt` file only proves *identity* (public claim). To **connect**, a client also needs the
matching **private nkey seed**. `nsc generate creds` bundles both into one file.

```bash
nsc generate creds --account company-a --name publisher     > creds/publisher.creds
nsc generate creds --account company-a --name subscriber     > creds/subscriber.creds
nsc generate creds --account company-b --name notification   > creds/notification.creds
```

A `.creds` file looks like:

```
-----BEGIN NATS USER JWT-----
eyJ0eXAiOiJKV1Qi...
------END NATS USER JWT------

-----BEGIN USER NKEY SEED-----
SUAIO3FHUX5PNV2LQIIP7TZ3N4L7...
------END USER NKEY SEED------
```

- **Top block** = the JWT (public identity claim).
- **Bottom block** = the private seed, used to sign a server-issued challenge (nonce) during
  connection — it proves ownership of the identity without ever transmitting the private key
  itself.

> ⚠️ **`.creds` files contain private keys. Never commit them to git.**

```bash
echo "jwt_auth/creds/" >> ../.gitignore
chmod 600 creds/*.creds
```

> **Important:** Any time you change a user's permissions with `nsc edit user`, the JWT
> changes — you must **regenerate the `.creds` file** for that user, or the client will keep
> using stale (old) permissions.

---

### Step 5 — Write the server config (`configs/server.conf`)

```conf
# Basic server settings
listen: 0.0.0.0:4222
server_name: jwt-auth-server

# Point to the Operator JWT - this is the root of trust.
# The server will only accept Account/User JWTs signed by this operator's key.
operator: "./operator/operator.jwt"

# Full resolver: the server stores/looks up Account JWTs in a local directory.
# 'nsc push' populates this directory live over the network via the SYS account.
resolver: {
  type: full
  dir: "./configs/jwt-store"
  allow_delete: false
  interval: "2m"
  timeout: "1.9s"
}

# Optional: preload account JWTs at startup (fallback if push hasn't happened yet)
resolver_preload: {}
```

**Key settings explained:**

| Setting | Meaning |
|---|---|
| `operator` | Path to the trusted Operator JWT. Anything not signed by this operator (or its signing key) is rejected. |
| `resolver.type: full` | The server persists account JWTs to a local directory and watches it for updates — this is the "decentralized" piece: no restart needed to add/update tenants. |
| `resolver.dir` | Where account JWTs are stored on disk, named `<account-public-key>.jwt`. |
| `resolver.interval` | How often the server re-checks for expired/updated JWTs. |


Tell `nsc` where to push account JWTs to (so `nsc push` knows the target server):

```bash
nsc edit operator --account-jwt-server-url nats://localhost:4222
nsc describe operator --raw > operator/operator.jwt   # re-export after edit!
```

---

### Step 6 — Start the server

```bash
nats-server -c configs/server.conf
```

Watch for these confirmations in the startup logs:
- `Trusted Operators` → shows `MyOperator` loaded
- `Managing all jwt in exclusive directory ...jwt-store` → resolver active
- `Listening for client connections on 0.0.0.0:4222`
- `Server is ready`

**Leave this running** in its own terminal — it's your live server for everything below.

---

### Step 7 — Push Account JWTs to the live server (in a new terminal)

```bash
nsc push --all
```

**What this does:** connects to the running server (using the `SYS` account's admin
credentials, over the URL configured in Step 5) and pushes the `SYS`, `company-a`, and
`company-b` JWTs into `configs/jwt-store/`. The server picks these up **live, with no
restart**. This is the actual mechanism that makes the whole thing "decentralized" —
accounts can be added/updated/revoked on a running server just by pushing new JWTs.

Verify:

```bash
ls -la configs/jwt-store/
```

You should see one `.jwt` file per account, named by its public key.

---

### Step 8 — Test with the `nats` CLI

**Terminal — subscribe as `subscriber`:**

```bash
nats sub "app.>" --creds creds/subscriber.creds -s nats://localhost:4222
```

**Terminal — publish as `publisher`:**

```bash
nats pub "app.test" "hello from publisher" --creds creds/publisher.creds -s nats://localhost:4222
```

If the subscriber terminal shows the message, the full chain (**Operator → company-a →
publisher/subscriber**) is verified and working.

**Prove tenant isolation:**

```bash
nats sub "app.>" --creds creds/notification.creds -s nats://localhost:4222
```

Publish again as `publisher` — `notification` (in `company-b`) will receive **nothing**, even
though it's subscribed to the identical subject pattern. Accounts are fully isolated subject
spaces by default.

---

### Step 9 — Cross-account communication (export/import)

To let `company-b` selectively receive specific events from `company-a`:

```bash
# On company-a: declare what's shareable
nsc add export --account company-a --subject "app.events.>" --name company-a-events

# On company-b: opt in to receive it
nsc add import --account company-b --src-account company-a --remote-subject "app.events.>"

# Push the updated JWTs live
nsc push --all
```

- **Export** = "I'm willing to share `app.events.>` with accounts that import it." (Public by
  default — any account can import if it knows the subject. For tighter control, use a
  **private** export with a signed activation token issued only to specific accounts.)
- **Import** = "map `company-a`'s exported subject into my own subject space."

**Test:**

```bash
# notification (company-b) listening
nats sub "app.>" --creds creds/notification.creds -s nats://localhost:4222

# publisher (company-a) sends to the exported subject
nats pub "app.events.order_created" "New order #123" --creds creds/publisher.creds -s nats://localhost:4222
```

`notification` **will** receive this (only because `app.events.>` was explicitly exported and
imported). Plain `app.test` traffic in `company-a` still stays invisible to `company-b`.

---

### Step 10 — Lock down permissions (least privilege)

By default every user can pub/sub to anything in their account. Restrict each to only what
it actually needs:

```bash
# publisher: can publish, cannot subscribe
nsc edit user --account company-a publisher \
  --allow-pub "app.>" \
  --deny-sub "app.>"

# subscriber: can only subscribe to app.order.>, cannot publish
nsc edit user --account company-a subscriber \
  --allow-sub "app.order.>" \
  --deny-pub "app.>"

# notification: can only subscribe to the imported events subject, cannot publish at all
nsc edit user --account company-b notification \
  --allow-sub "app.events.>" \
  --deny-pub ">"
```

**Final permission matrix:**

| User | Account | Can Publish | Can Subscribe |
|---|---|---|---|
| `publisher` | company-a | `app.>` | ❌ (denied) |
| `subscriber` | company-a | ❌ (denied) | `app.order.>` only |
| `notification` | company-b | ❌ (denied, all subjects) | `app.events.>` only |

> ⚠️ **After every `nsc edit user`, you must regenerate that user's `.creds` file** —
> permissions are baked into the JWT, and the old `.creds` file still has the old (looser)
> permission set until regenerated.

```bash
nsc generate creds --account company-a --name publisher     > creds/publisher.creds
nsc generate creds --account company-a --name subscriber     > creds/subscriber.creds
nsc generate creds --account company-b --name notification   > creds/notification.creds
nsc push --all
```

Verify any user's current permissions at any time:

```bash
nsc describe user --account company-a subscriber
```

Look at the `Pub Allow/Deny` and `Sub Allow/Deny` fields.

---

## 5. Python Clients

Install the library:

```bash
pip install nats-py
```

All three scripts follow the same pattern — `user_credentials="creds/<name>.creds"` handles
the entire JWT handshake automatically (reads the JWT, signs the server's nonce challenge with
the embedded private seed). You never manually touch the JWT contents in code.

| Script | Identity | Account | Behavior |
|---|---|---|---|
| `publisher.py` | publisher | company-a | Publishes one message to `app.test` (or `app.order.*` / `app.events.*` depending on what you're testing) and exits |
| `subscriber.py` | subscriber | company-a | Subscribes to `app.>` in code, but server permissions only actually deliver `app.order.>` messages |
| `notification.py` | notification | company-b | Subscribes to `app.>` in code, but server permissions only actually deliver the imported `app.events.>` messages |

Run them:

```bash
# Terminal 1
python subscriber.py

# Terminal 2
python notification.py

# Terminal 3
python publisher.py
```

Even though the subscriber scripts subscribe broadly (`app.>`), the **server enforces the real
boundary** — permission scoping happens server-side via the JWT, not client-side. This is an
important security property: a compromised or buggy client cannot subscribe its way around
its own permissions.

---

## 6. Quick Reference — Common Operations

### Add a new tenant (account)

```bash
nsc add account --name company-c
nsc edit account company-c --sk generate
nsc push --all
```

No server restart needed — the resolver picks it up live.

### Add a new user to an existing account

```bash
nsc add user --account company-a --name new-service
nsc edit user --account company-a new-service --allow-pub "app.foo.>" --allow-sub "app.bar.>"
nsc generate creds --account company-a --name new-service > creds/new-service.creds
nsc push --all
```

### Revoke a user

```bash
nsc revoke add user --account company-a publisher
nsc push --all
```

### Inspect the whole trust chain at a glance

```bash
nsc describe operator
nsc list accounts
nsc list users --account company-a
nsc describe user --account company-a publisher
```

### Rebuild everything from scratch

If you ever want to tear down and redo this exercise for learning:

```bash
rm -rf ~/.local/share/nats/nsc ~/.local/share/nats/nkeys
```

**What this does:** wipes `nsc`'s entire local store (all operators/accounts/users/keys it
knows about). Then repeat Steps 1–10 above from the top.

---

## 7. Troubleshooting Notes (things we actually hit)

| Problem | Cause | Fix |
|---|---|---|
| `Parse error on line N: 'Floats must start with a digit'` | Unquoted config value starting with `.` (e.g. `./operator/operator.jwt`) — parser tries to read it as a number | Wrap the value in double quotes: `operator: "./operator/operator.jwt"` |
| Client connects but sees nothing / can't publish | Permissions changed via `nsc edit user` but `.creds` file wasn't regenerated | Re-run `nsc generate creds` for that user, then `nsc push --all` |
| Account JWT changes not visible on the running server | Forgot to `nsc push --all` after `nsc add/edit account` or `nsc add export/import` | Always `nsc push --all` after any account/user edit |
| Operator JWT on disk out of date | `nsc edit operator` was run but `operator/operator.jwt` wasn't re-exported | Re-run `nsc describe operator --raw > operator/operator.jwt` after every operator edit |

---

## 8. Summary — The Mental Model to Remember

1. **Operator** = root of trust, one per deployment. Server only needs the operator's public
   key.
2. **Account** = isolated tenant. Subjects are invisible across accounts unless explicitly
   exported/imported.
3. **User** = individual client identity, scoped with pub/sub permissions.
4. **`.jwt` files** = public identity claims (safe to store, not secret).
5. **`.creds` files** = JWT + private nkey seed (secret, never commit).
6. **`nsc push`** = the live sync mechanism — edits to accounts/users propagate to a running
   server without restart, which is what makes this "decentralized."
7. **Permissions live in the JWT**, not in server config — so any permission change requires
   regenerating `.creds` and re-pushing.