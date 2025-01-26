# linkedin.com
### Why do we need this system?
To communicate with people, for networking, watch other people success, to be more valuable for HR, to find job. If user is HR to find new employees.

### Functional requirements
1. Registration, login
2. Search users, posts, hashtags, jobs, employees
3. Connect to people, follow and unfollow people, building network
4. Messaging with people
5. Creating posts, comments, likes
6. Adding information about work experience, education, skills etc.
7. Notifications (new posts, likes, comments, messages)
8. Hiring people, creating job offers, job ads
9. Posting events
10. Premium subscription: people that visited profile, insights about companies

### Non-functional requirements:
1. Very consistent way of verification, logging in, restoring account  
1. DAU [150M users](https://www.linkedin.com/pulse/daily-active-users-dau-joyce-j-shen/#:~:text=members%20and%20over-,140%20million%20DAU,-.%20So%20this%20is)
2. [12M RPS](https://newsletter.systemdesigncodex.com/p/how-linkedin-authorizes-10-million), as article is almost one year old, and considering some additional capacity 12M RPS should be correct value
3. DOM content load less than 1000ms, general load less than 5000ms
4. RTT less than 200ms for North America and Europe and no more than 400ms for any other region
5. Adaptive layout
6. No less than 99.9% uptime, as it is a networking/hiring app I think this should not be too critical
7. To decrease RTT and improve performance, using CDN
8. Portability - mobile, desktop and web versions
9. Feed personalization


### CAP theorem
In my opinion AP is more suitable for chats, posts, coments, etc. Because it is better to have option to write and send message even if network is inaccessible, user can later connect to the internet or wait for server availabiblity for messages to be sent. There is only one service where CP is suitable - buying premium subscription.
