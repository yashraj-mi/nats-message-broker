# NATS Message Broker - Tasks & Assignments

## 📌 Repo Information

This Repo contains all of my **NATS Message Broker** related work, including:

- ✅ Practice tasks
- ✅ Assignments
- ✅ Learning exercises

---

# What is NATS?

**NATS** is a lightweight, high-performance messaging system designed for cloud-native applications, microservices, and distributed systems.

It enables applications to communicate efficiently using asynchronous messaging with very low latency.

### Key Features

- 🚀 High performance
- ⚡ Low latency
- 🔄 Asynchronous communication
- 📡 Publish/Subscribe messaging
- 📬 Request/Reply messaging
- 🌍 Distributed architecture
- 🔒 Secure communication (TLS, Authentication)
- 📈 Scalable and reliable

---

# NATS Messaging Patterns

## 1. Publish / Subscribe (Pub/Sub)

A publisher sends messages to a subject, and all subscribers listening to that subject receive the message.

Example:

Publisher

```
Publish -> orders.created
```

Subscribers

```
Subscribe -> orders.created
```

Use Cases:

- Notifications
- Event broadcasting
- Real-time updates

---

## 2. Request / Reply

A client sends a request and waits for a response from a service.

```
Client
   |
Request
   |
Server
   |
Reply
   |
Client
```

Use Cases:

- API communication
- Microservice interaction
- RPC (Remote Procedure Calls)

---

## 3. Queue Groups

Multiple subscribers join the same queue group.

Each published message is delivered to **only one** member of the group, enabling load balancing.

```
Publisher
     |
orders.process

Worker 1
Worker 2
Worker 3
```

Only one worker processes each message.

Use Cases:

- Worker pools
- Background jobs
- Task processing

---

# Basic NATS Concepts


| Concept     | Description                          |
| ----------- | ------------------------------------ |
| Server      | NATS server that routes messages     |
| Client      | Application connected to NATS        |
| Subject     | Topic/channel used for communication |
| Publisher   | Sends messages                       |
| Subscriber  | Receives messages                    |
| Queue Group | Load-balanced subscribers            |
| Requester   | Sends requests                       |
| Responder   | Replies to requests                  |

---

# References

- https://nats.io/
- https://docs.nats.io/
