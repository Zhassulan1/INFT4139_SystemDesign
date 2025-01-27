# halyk

### Why do we need this system?
To make transactions, to send money, to get salaries, etc. Mostly it acts as buffer to receive money to send later to other bank accounts.

### Functional requirements

1. Send/receive money
2. See balance

### Non-functional requirements

1. MOU is around 12M users, each on average make 4 transactions per month.
2. Load has peaks At the end and at the beginning of the month. Let's assume that 80% of load is during first 10 and last 5 days of the month. During night significantly lower RPS.
3. 48M transactions in 15 days = 3.2M transactions per day, 74 transactions per second (only daytime counted). At peak 500 transactions per second.
4. Each transaction 1 KB, 500KB/s bandwidth.
5. 12M * 4 * 1KB = 48GB/month data. For 5 years 2880GB. With backups 8640GB.
6. 4 vCPU, 4GB RAM, 10 TB HDD

### CAP theorem
CP is better choice. Because there shouldn't be withdrawal of not existing money.