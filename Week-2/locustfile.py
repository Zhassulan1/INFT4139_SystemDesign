"""
for python 10 workers
for golang 15 workers
"""

from locust import FastHttpUser, task, constant
# import random
# import string
import secrets

def register(client, name, password):
    response = client.post("/user", json={"name": name, "password": password})
    try:
        data = response.json()
    except Exception as e:
        print("\n\n\nError parsing response:")
        raise e

    if response.status_code > 201:
        print(f"Registration failed with status code: {response.status_code}")
        print(response.text)
    return data.get("user_id")

class User(FastHttpUser):
    wait_time = constant(0)
    
    def on_start(self):
        self.name = secrets.token_hex(10)
        self.password = secrets.token_hex(10)

        self.user_id = int(register(self.client, self.name, self.password))
        self.token = None

    @task
    def check_token(self):
        response = self.client.post(
            "/token",
            json={
                "user_id": self.user_id,
                "password": self.password
            },
        )

        self.token = response.json()["access_token"]

        self.client.get(
            "/check",
            headers={"Authorization": f"Bearer {self.token}"},
            # json={"user_id": self.user_id},
        )
