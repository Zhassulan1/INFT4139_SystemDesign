from locust import FastHttpUser, task, constant
from random import randint
import redis

# pool = redis.ConnectionPool(host='localhost', port=6379, db=1, max_connections=1000)
r = redis.Redis(host='localhost', port=6379, db=1)

def get_user_id():
    data = r.get("user_id")

    if not data:
        user_id = 1
    else:
        user_id = int(data.decode()) + 1

    r.set("user_id", user_id)
    return user_id



class User(FastHttpUser):
    wait_time = constant(0)
    
    def on_start(self):
        # response = self.client.get(
        #     "/user_id",
        # )
        # print("Response:", response.json())
        # self.user_id = response.json()["user_id"]
        self.user_id = get_user_id()
        self.token = None
        print(self.user_id)


    @task
    def check_token(self):
        response = self.client.post(
            "/token",
            json={"user_id": self.user_id},
        )
        self.token = response.json()["token"]

        self.client.post(
            "/check",
            headers={"Authorization": self.token},
            json={"user_id": self.user_id},
        )
