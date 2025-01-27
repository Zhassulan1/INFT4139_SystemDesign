# telegram

### Why do we need this system?
To send messages, to chat with people, to read channels

### Functional requirements
1. Registration, login, 2FA
2. Chat, group chat
3. Channels: posts, texts
4. Secure chats
5. Stories

### Non-functional requirements:
1. Response time less than 200ms
2. DAU 450M. [15M messages sent every day](https://telegram.org/blog/15-billion#:~:text=is%20delivering%20over-,15%20billion%20messages,-daily%20%E2%80%93%20that%27s%20roughly) (text, files, stickers, etc). 
    
    Assume that average size of message is 10KB. That is ~= 2MB/s. But  this bandwidth is not enough, because you can't wait half day long just to send 2GB file. So, 1/3 000 000 of messages sent is big file, 5 * 200 = 1 TB/s bandwidth is required.

    We can also balance that with quotas for upload speed

3. As we want to reserve 1 TB/s banddwidth:

    One 64 bit 5GHz CPU can process 64 * 5 = 320 Billion bits/second = 40GB/s. To process 1 TB/second we need 10^12 / 4 * 10^10 = 250 CPU cores.


5. 1TB/s: 64GB DDR5 RAM * 1500 ~= 1PB of RAM

4. For all data above we need to be stored with 5 years capacity 274 TB storage is needed.

    With backups and replication we need 274 * 3 = 822 TB


### CAP theorem
In my opinion AP is more suitable for this. Because users seeing slightly different comments, messages, emojis, etc. is not a big problem.