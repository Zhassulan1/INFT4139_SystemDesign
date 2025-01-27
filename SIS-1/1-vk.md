# vk.com
### Why do we need this system?

To communicate with friends, to see memes and news from different communities. To watch videos from russian channels that were deleted from youtube (наука 2.0 as example). To share photos and videos. To watch some clone of tiktok called clips. To listen music.

### Functional requirements
1. Registration, login
2. Search users, communities, posts, music, hashtags
3. follow and unfollow communities, add to friends, remove from friends
3. Chat, with possibility to send text, audio, video, circles, reactions to messages, stickers, also sharing internal content like posts (music, clips, etc.)
4. Posts - albums that can contain one or more of: images, videos, music (posted audio is stored as music), text, clips.
5. Comments and likes under posts
6. Profile settings: Personal information, privacy and visibility, blacklists
7. Notifications (new posts, likes, comments, replies, messages)
8. Groups - chat with multiple users
9. Auth using vk.com to other sites and services
10. Managing advertisement for business customers
10. Posting stories
11. "Services" (some kind of extensions/plugins): Games and other apps
12. vk pay
    * creating and managing wallets
    * transferring money
13. vk market
    * buying products, orders
    * bookmarking products
    * reviews for products
14. Media editor, to edit media files before posting and sending to chat
15. Buying stickers and gifts using votes (internal currency)
16. Services for FSB and KGB to stalk users activity and listen microphone if available 


### Non-functional requirements:
1. Security: csrf, xss, sql injection, etc.
2. DAU: [75M users](https://www.statista.com/statistics/1113226/vk-daily-active-users-via-mobile/) with addidtional capacity for future growth
3. RPS: [200k for images](https://habr.com/ru/companies/vk/articles/594633/#:~:text=RPS%20%D1%81%201%20%D0%BC%D0%BB%D0%BD%20%D0%B4%D0%BE%20160%20%D1%82%D1%8B%D1%81%D1%8F%D1%87), [2M total](https://fomag.ru/news-streem/nagruzka-na-servery-vkontakte-za-2024-god-uvelichilas-na-35-vk-video-vtroe/#:~:text=%D0%B1%D0%BE%D0%BB%D0%B5%D0%B5%20%D0%B4%D0%B2%D1%83%D1%85%20%D0%BC%D0%B8%D0%BB%D0%BB%D0%B8%D0%BE%D0%BD%D0%BE%D0%B2%20%D0%BF%D0%BE%D0%BB%D1%8C%D0%B7%D0%BE%D0%B2%D0%B0%D1%82%D0%B5%D0%BB%D1%8C%D1%81%D0%BA%D0%B8%D1%85%20%D0%B7%D0%B0%D0%BF%D1%80%D0%BE%D1%81%D0%BE%D0%B2%20%D0%B2%20%D1%81%D0%B5%D0%BA%D1%83%D0%BD%D0%B4%D1%83)
4. DOM content load less than 1000ms
5. [RTT](https://habr.com/ru/companies/vk/articles/594633/#:~:text=%D0%BF%D0%B5%D1%80%D1%86%D0%B5%D0%BD%D1%82%D0%B8%D0%BB%D1%8C%20%D0%B1%D1%83%D0%B4%D0%B5%D1%82%20%D1%80%D0%B0%D0%B2%D0%B5%D0%BD-,300,-%D0%BC%D1%81.%20%D0%A2%D0%BE%20%D0%B5%D1%81%D1%82%D1%8C) less than 200ms for Eurasia and no more than 400ms for any other region
6. Adaptive layout
7. No less than 99.9% uptime, as it is social media app I think this should be enough (~8h down per year)
8. Availability: using CDN for images and videos ([for example vk has more than 50](https://habr.com/ru/companies/vk/articles/575358/#:~:text=%D1%83%20%D0%92%D0%9A%D0%BE%D0%BD%D1%82%D0%B0%D0%BA%D1%82%D0%B5%20%D0%B1%D0%BE%D0%BB%D1%8C%D1%88%D0%B5-,50%20CDN%2D%D0%BF%D0%BB%D0%BE%D1%89%D0%B0%D0%B4%D0%BE%D0%BA,-%2C%20%D0%BD%D0%BE%20%D0%B4%D0%BB%D1%8F%20%D1%80%D0%B0%D0%B7%D0%BC%D0%B5%D1%89%D0%B5%D0%BD%D0%B8%D1%8F))
9. Portability - mobile, desktop and web versions
10. User feed personalization
11. 6.3 Billon images/video, on average +6 every second. Assuming that average size of media file is 5MB, it is 30MB/s

    For 5 years it is around 900 Million photos/videos, 4 PB of data in 5 years. Text messages and DB is way less, so it'll be ignored

12. Considering backups and replication, we need 4 * 3 = 12 PB of storage. 
13. At this point there should be used something like Amazon Glacier for rarely accessed data
14. 1M RPS each on average 0.2KB = 200GB/s bandwith:
    
        0.2 * 10^12 / 64 * 10^9 = 3125 RAM modules
        3125 * 64GB = 200TB RAM

15. One 64 bit 5GHz CPU can process 64 * 5 = 320 Billion bits/second = 40GB/s. To process 200GB/second we need  20 * 10^10 / 4 * 10^10 = 5 CPU cores.

    *(That is calculated for high performance gaming CPU, server cpu is like 5-8 times slower)*



### CAP theorem

In my opinion AP is more suitable for chats, posts, coments, etc. Because it is better to have option to write and send message even if network is inaccessible, user can later connect to the internet or wait for server availabiblity for messages to be sent.  But for other services that work with financial transactions like vk pay, or vk market it is better to have CP. To avoid problems like double payments, or withdrawals of not existing money.