# instagram

### Why do we need this system?
To post photos videos, send messages, follow people, like posts, comment on posts, search for people

### Functional requirements
2. Sending messages
1. Posting photos/videos
4. Liking posts
5. Commenting on posts
6. Searching for people
3. Following people


### Non-functional requirements:
1. DOM content load less than 5000ms
2. Adaptive layout
3. Response time less than 200ms
4. DAU 500M, over [1M RPS (2015)](https://instagram-engineering.com/instagration-pt-2-scaling-our-infrastructure-to-multiple-data-centers-5745cbad7834#:~:text=million%20requests%20per%20second), let's say 4M for 2025 (it scaled [4 times](https://www.google.com/search?q=how+many+dau+does+instagram+have&oq=how+many+dau+does+instagram+have&gs_lcrp=EgZjaHJvbWUqCAgAEEUYJxg7MggIABBFGCcYOzIGCAEQRRhAMgYIAhAjGCcyBwgDEAAYgAQyCQgEEAAYChiABDIJCAUQABgKGIAEMgcIBhAAGIAEMgcIBxAAGIAE0gEJMTMxNTVqMGo3qAIAsAIA&sourceid=chrome&ie=UTF-8#:~:text=With-,2%20billion,-monthly%20active%20users))
5. 40 billion photos/videos overall, [+95million monthly](https://www.wordstream.com/blog/ws/2017/04/20/instagram-statistics#:~:text=per%20day.%0A8.-,95%20million%20photos,-and%20videos%20are), which is +37 every second. Assuming that average size of media file is 5MB, it is 185MB/s. 

    For 5 years it is 5,7 Billion photos/videos, 28,5 PB of data in 5 years. Text messages and DB is way less, so it'll be ignored

6. Considering backups and replication, we need 28.5 * 3 = 85.5 PB of storage
7. At this point there should be used something like Amazon Glacier for rarely accessed data
6. 1M RPS each on average 1KB = 1TB/s bandwith

        1 * 10^12 / 64 * 10^9  = 15625 RAM modules
        64GB DDR5 * 15625 ~= 1PB of RAM

7. One 64 bit 5GHz CPU can process 64 * 5 = 320 Billion bits/second = 40GB/s. To process 1 TB/second we need 10^12 / 4 * 10^10 = 25 CPU cores.

    *(That is calculated for high performance gaming CPU, server cpu is like 5-8 times slower)*

### CAP theorem
In my opinion AP is more suitable for this. Because users seeing slightly different comments, titles, likes, etc. is not a big problem. But data availability is very important, it has more priority than data being up to date