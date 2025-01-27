# kaspi

### Why do we need this system?
To make transactions, to send money, to get salaries, etc. Mostly it acts as buffer to receive money to send later to other bank accounts.

### Functional requirements

1. Send/receive money
2. See balance


### Non-functional requirements
1. MOU is around [10M users](https://kase.kz/files/emitters/CSBN/csbnp_2019_rus.pdf) (extropolated data from 2019) each on average make 30 transactions per month.
2. Load has peaks At the end and at the beginning of the month. Also peaks during "Kaspi Zhuma". Let's assume that 65% of load is during first 10 and last 5 days of the month. During night significantly lower RPS.
3. 300M transactions =  10M transactions per day, 232 transactions per second (only daytime counted). 
4. During "Kaspi Zhuma" at peak 2000 transactions per second.
4. Each transaction 1 KB, 2GB/s bandwidth.
5. 300M * 1KB = 300GB/month data. For 5 years 36TB. With backups 108TB.
6. 16 vCPU, 64GB RAM, 100 TB HDD and 100 GB SSD for paek load.


### CAP theorem
CP is better choice. Because there shouldn't be withdrawal of not existing money.