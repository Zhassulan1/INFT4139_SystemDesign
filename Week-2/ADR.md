# Using Fastapi, PostgreSQL and Redis to manage tokens (Python)

## Status

Accepted

## Context

Under the pressure of deadlines student had to create simple token management system.

I needed to build an simple and efficient oauth based token management system that supports JWT-based authentication. The service must handle token creation, validation, and expiration in a performant manner while also managing user data securely. There was not much time, but a lot of work and testing to do. System will serve 1000 users and will handle a load of 20000 requests per second.

## Decision

We decided to implement the authentication service using FastAPI for the API layer and Redis for JWT token storage, with user data maintained in PostgreSQL via psycopg2.

**FastAPI:**

* Asynchronous and High Performance: FastAPI uses asynchronous programming, which allows it to handle a large number of concurrent requests.

- Developer Productivity: FastAPI offers automatic generation of OpenAPI and JSON Schema, built-in validation, and dependency injection. These features reduce boilerplate code and accelerate development.

- Modern Python Features: It utilizes modern Python type hints, leading to improved code quality and maintainability.


**Redis:**

- Low Latency and High Throughput - Redis provides extremely fast read/write operations and is well‑suited for caching and session management.

- Built-in Expiration: Redis natively supports key expiration, making it useful invalidate tokens. This reduces the need for cleanup logic in the application.


**PostgreSQL with psycopg2:**

- Data Integrity and Security: PostgreSQL offers ACID properties, which are useful for managing sensitive user information.

- Reliability: The psycopg2 adapter is a well-supported PostgreSQL driver, ensuring reliable communication with the database.

## Consequences

**Positive Outcomes:**

 - Enhanced Performance: The asynchronous FastAPI and Redis's fast in-memory data storing gives low-latency responses under high load.

- Efficient Session Management: Redis's built-in expiration mechanism simplifies token lifecycle management, reducing application complexity.

- Rapid Development and Maintainability: FastAPI's automatic documentation speed up development, testing.

- Robust Security: User data is stored securely in PostgreSQL.

**Negative Outcomes:**

- Operational Complexity: Maintaining and orchestrating two distinct databases (Redis for JWT tokens and PostgreSQL for user data) introduces additional operational complexity.

- Monitoring and Debugging: Coordinating logs, metrics, and error tracking across multiple services requires careful design and monitoring tools to ensure smooth operation.

Overall, the use of FastAPI and Redis with PostgreSQL for persistent storage, effective, scalable, and maintainable solution for our authentication service. 