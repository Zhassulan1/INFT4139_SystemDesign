# Using Fastapi and Redis to manage tokens (Python)

## Status
Accepted

## Context
Under the pressure of deadlines student had to create simple token management system. There was not much time, but a lot of work and testing to do. System will serve 1000 users and will handle a load of 20000 requests per second.

## Decision
I decided to adopt FastAPI for building our API endpoints and Redis as our in-memory datastore for token management. The main reasons for this decision include:

FastAPI Advantages:
Asynchronous Support - FastAPI natively supports async endpoints.

Performance - FastAPI is designed for high performance and low latency.

Redis Advantages:
Low Latency and High Throughput - Redis provides extremely fast read/write operations and is well‑suited for caching and session management.

Built‑in Expiry Mechanism: The ability to set key expirations (e.g., using the SETEX command) is ideal for managing tokens that must expire automatically after a given period.


## Consequences
What Becomes Easier:

High Concurrency and Throughput - With asynchronous request handling in FastAPI and connection pooling in Redis, the system can handle a higher number of requests per second (RPS) with reduced latency.

Token Expiry - Redis’ native key expiration features simplify token lifecycle management without additional overhead in the application code.

What Becomes More Difficult:

Operational Complexity - Introducing Redis (especially in a clustered or production environment) may require additional operational considerations such as monitoring, backup, and scaling.

Overall, the combination of FastAPI and Redis addresses the performance bottlenecks while introducing manageable operational complexity, making it the best fit for token management needs.

