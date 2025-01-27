# bitly

### Why do we need this system?
To shorten links, to generate qr codes for links

### Functional requirements
1. Map link to short link
2. Redirect short link to original link
3. QR code: create short link, create qr code for short link

### Non-functional requirements:
1. 256M uses (link/qr code generations) per month - 96 uses per second
2. 256 * 10^6 * 1000 = 256 GB of data per month, 15 TB of storage is enough for 5 years (without growth, or if old links are deleted automatically).
3. It all can be done in one database, one table with hash index enabled. It is able to process 96 requests per second. Probable average length of link might be 1000 ASCII characters which is 1 MB.
4. 10B clicks and scans per month, 4823 select queries per second. Probably 5GB of data per second is transfered.
5. 16 GB RAM "Just in case" of some unexpected load.
6. 4 vCPU should be enough if one for OS, other for application itself.
7. Replication of data. If we decide to store 3 copies, it is 45 TB of storage.

### CAP theorem
In my opinion CP is more suitable for this system. Because if we do not have access to the database, we should not generate or open short link and qr code. We can't risk giving inconsistent information for users.