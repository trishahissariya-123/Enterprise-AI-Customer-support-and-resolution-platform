from locust import HttpUser, task, between

class SupportAPIUser(HttpUser):
    wait_time = between(1,2)

    @task
    def get_transactions(self):
        self.client.get(
            "/api/v1/customers/CUST1001/wallet"
        )

