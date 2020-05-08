from locust import HttpLocust, TaskSet, seq_task, between
from locust.exception import StopLocust

JURISDICTIONS = [f"foo{i}@example.com" for i in range(100)]


class JurisdictionAdmin(TaskSet):
    def on_start(self):
        self.email = JURISDICTIONS.pop()
        print(f"STARTING {self.email}")

    @seq_task(1)
    def login(self):
        print(f"{self} {self.email} logging in")

    @seq_task(2)
    def upload_manifest(self):
        print(f"{self} {self.email} uploading manifest")

    @seq_task(3)
    def finish(self):
        print(f"{self} {self.email} stopping")
        raise StopLocust()


class User(HttpLocust):
    task_set = JurisdictionAdmin
    wait_time = between(1, 2)

    def setup(self):
        print("setting up: log in as audit admin and create an election")
