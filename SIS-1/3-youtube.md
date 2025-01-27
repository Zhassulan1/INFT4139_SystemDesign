# youtube

### Why do we need this system?
To watch videos, to learn

### Functional requirements
1. Registration, login
2. Search videos, playlists, channels
3. Watching videos
6. Commenting, Likes, Dislikes
4. Creating playlists, adding videos to playlists
5. Subscribing to channels


### Non-functional requirements:
1. DAU [83M users](https://backlinko.com/youtube-users) Which is average of ~1000 users per second
2. Current storage size [20 petabytes](https://toptechnova.com/how-much-data-storage-does-youtube-use#:~:text=library%20stretches%20over-,20%20petabytes,-.). Let's assume that every year it increases by 10%, so, for 5 years it will be 20 * 1.1^5 = 32.21 PB. We need 32.21 PB capacity for 5 years.
3. Average youtube page opening has 70 requests in 10 seconds = 7 requests per second from one user.
5. Average user spends 50 min per day on youtube.
2. I consider that each page loaded by simple HTTP requests without maintaining connection like websocket
4. Average video page will transfer 30 MB of data in 40 seconds = 0.75 MB per second (peak for one user). Adding video (full hd and 4k) 0.43 - 1 MB/sec (till the rest of video). Per day each user will transfer 50 * 60 * 1 = 3GB of data. That is 3 TB per second overall.
7. One 64 bit 5GHz CPU can process 64 * 5 = 320 Billion bits/second = 40GB/s. To process 3 TB/second we need 3 * 10^12 / 4 * 10^10 = 750 CPU cores.
8. We also need RAM that can read/write 3TB/second. DDR5 can read/write around 64 GB/s. We need 3 * 10^12 / 64 * 10^9 = 46875 RAM modules, where every module can store 64 GB.
9. Replication of data. 3 copies of data should be stored in case we do not consider ways of storing data like btrfs or rsync.


### Cap theorem 
In my opinion AP is more suitable for this. Because users seeing slightly different comments, titles, likes, dislikes, etc. is not a big problem. But data availability is very important, it has more priority than data being up to date