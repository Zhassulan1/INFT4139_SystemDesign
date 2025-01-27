# WSP

### Why do we need this system?
To register for disciplines, to see schedule, to mark online attendance, to form schedule, to read KBTU news, Add/Droping disciplines, inquiries

### Functional requirements
1. Forming schedule
2. Registering for disciplines
3. Adding/dropping disciplines
3. Viewing schedule
4. Marking online attendance
5. Requesting inquiries
5. Reading news


### Non-functional requirements:
1. DOM content load less than 500ms, general load less than 2000ms
2. Adaptive layout
3. Response time less than 200ms, during peak load < 500ms
4. 50 GB for DB, and for file storage 500 GB
5. HDD 500 GB x 3 (for backups/RAID array), SSD 50-150 GB for DB
7. As peak load might be 3k users (75% of all) during registration. Probably 2000 of them will send requests at the same time. As it is just HTTP requests (not file), 2000 rps each probably weight ~= 0.5KB. 2000 * 0.5 = 1 MB/s. Also pages on average weight 50-70KB * 2000 = 100-140 MB/s. So, 100-140 MB/s + 1 MB/s = 100-140 MB/s. 140MB/s * 8 = 1120 Mbps. 1Gb/s bandwith is enough.
8. RAM 4 GB DDR4 is enough.
9. 2 vCPU
