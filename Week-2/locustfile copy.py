from locust import HttpUser, task, between
from random import randint 


class User(HttpUser):
    # wait_time = between(1, 5)
    @task
    def get_token(self):
        TOKEN = "7184808c5349a7a26aca59d7dc6dc8c97c2754ddce298a11c587ea0cdf4ec9f73e0f15a714e0c8e79ebfbe5771b7d6745e31"
        token = self.client.post(
            "/token",
            json={"user_id": randint(1, 1000)}
            # headers={"Authorization": TOKEN}
        )
        try:
            TOKEN = token.json()["token"]
        except Exception as e:
            print("The value of token:", token)
            print("Token as text:", token.text)
            print("\n\n\nException itself: \n\n", e)
        # print(token.json()["token"])
        self.client.get(
            "/check",
            headers={"Authorization": TOKEN}
        )



# from locust import HttpUser, task, between
# from random import randint 


# class User(HttpUser):
#     # wait_time = between(1, 5)
#     @task
#     def get_token(self):
#         TOKEN = "7184808c5349a7a26aca59d7dc6dc8c97c2754ddce298a11c587ea0cdf4ec9f73e0f15a714e0c8e79ebfbe5771b7d6745e31"
#         token = self.client.post(
#             "/token",
#             json={"user_id": randint(1, 1000)}
#             # headers={"Authorization": TOKEN}
#         )
#         try:
#             TOKEN = token.json()["token"]
#         except Exception as e:
#             print("The value of token:", token)
#             print("Token as text:", token.text)
#             print("\n\n\nException itself: \n\n", e)
#         # print(token.json()["token"])
#         self.client.get(
#             "/check",
#             headers={"Authorization": TOKEN}
#         )