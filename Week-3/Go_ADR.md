# Using fasthttp, PostgreSQL and Redis to manage tokens (Go)

## Status

Accepted

## Context

Under the pressure of deadlines student had to create simple token management system.

I needed to build an simple and efficient oauth based token management system that supports JWT-based authentication. The service must handle token creation, validation, and expiration in a performant manner while also managing user data securely. There was not much time, but a lot of work and testing to do. System will serve 1000 users and will handle a load of at least 20000 requests per second.

## Decision

We decided to implement the authentication service in Go using the fasthttp framework for the API layer, PostgreSQL for persistent user data storage, and Redis for in-memory token management.

**fasthttp Framework:**

- High Performance: fasthttp is optimized for speed and low memory usage. 
- Minimal Overhead: Compared to other frameworks, fasthttp offers minimal abstractions, reducing the overhead.

**Redis:**

- Low Latency and High Throughput: Redis provides extremely fast read/write operations and is well‑suited for caching and session management.

- Built-in Expiration: Redis natively supports key expiration, making it useful invalidate tokens. This reduces the need for cleanup logic in the application.

**PostgreSQL:**

- Data Integrity and Security: PostgreSQL offers ACID properties, which are useful for managing sensitive user information.
- Reliability: The psycopg2 adapter is a well-supported PostgreSQL driver, ensuring reliable communication with the database.

## Consequences

**Positive Outcomes:**

- Enhanced Performance: The combination of fasthttp’s low overhead with Redis’s in-memory speed results in a system capable of handling over 20k requests per second with minimal latency.
- Efficient Token Lifecycle Management: Redis’s native support for key expiration simplifies token refresh and invalidation, reducing application complexity.

**Negative Outcomes:**

- Operational Complexity: Coordinating and maintaining two distinct components (Redis, and PostgreSQL) increases the overall complexity of the deployment and monitoring processes.

Overall, the decision to use fasthttp, PostgreSQL, and Redis provides a highly performant, scalable, and secure solution for our token management system. This architecture meets the demanding performance criteria while ensuring that the system remains maintainable and robust in production.
