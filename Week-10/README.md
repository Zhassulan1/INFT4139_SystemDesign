# Data Transfer

### 1. General approach
**For full copy for the first time** I select all rows from tables of database A, and insert to tables of database B.

**For synchronization**, I will use additional columns like `updated_at` and `created_at` to detect updated row or new row. We supposed that there are some ML model that gives all recommendations with the same `created_at` for all new rows. \
For example: new recommendations are ready at 01:20, and there are millions of rows with that `created_at`, we will launch updates at 01:21. As a result all rows with the same time are syncronised. 

To read data from Source DB we will use **Reapeatable Read** isolation level. so any updates during transaction are not selected.

`updated_at` column is just additional functionality in case some data analysts (or ML model) desides to update some recommendation after its creation.

**To speed up** the proccess I will use multiple worker instances for transaction.

**To maintain atomicity** I will use Saga pattern. Using Saga gives abbility to restart failed workers and be without worrying that there will be repeated rows.

### 2. Tools

Python, psycopg2.
Python because: lack of time, ease of use.
psycopg2 because: I am familiar with this library, and have used multiple times.

### 3. Key challenges
1. Transaction may fail.
2. All new rows with have same creation time.
3. There might be updates after creation.
4. Updates during synchronization or copying.
5. Workers may fail.




## How to run
Make sure that your Databases have folliwing tables, with same columns: [users](./migrations/users.sql), [products](./migrations/products.sql), [recommendations](./migrations/recommendations.sql).

To copy all rows from source to target:
~~~ bash
python db_transfer.py --mode copy --source source_db --target target_db
~~~
*(deletes old rows in target and inserts new rows from source)*


To run syncronization (updates and new rows):
~~~ bash
python db_transfer.py --mode sync --source source_db --target target_db
~~~


---
To fill db you can use [generate.sql](./migrations/generate.sql).