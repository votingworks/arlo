#
# A good way to run this script:
#
# locust -f first.py --host <host> --no-web -c 100 -r 10 --run-time 1m
#

from locust import HttpLocust, TaskSet, seq_task, between
from locust.exception import StopLocust
from pyquery import PyQuery
import json, uuid, time, csv

JSON_HEADERS = {"content-type": "application/json"}

CSV_HEADERS = {"content_type": "application/csv"}

JURISDICTIONS_FILE = "./jurisdictions.csv"
BIG_MANIFEST_FILE = "./big-manifest.csv"
SMALL_MANIFEST_FILE = "./small-manifest.csv"

j_reader = csv.reader(open(JURISDICTIONS_FILE, "r"))
JURISDICTIONS = [row[1] for row in j_reader][1:]


def get_auth(client):
    return json.loads(client.get("/auth/me").content)


def do_login(client, type, email):
    resp = client.get(f"/auth/{type}/start")

    # assume noauth extract the redirect_uri and state
    pq = PyQuery(resp.content)
    redirect_uri = pq("input[name=redirect_uri]")[0].value
    state = pq("input[name=state]")[0].value

    resp = client.post(
        "https://votingworks-noauth.herokuapp.com/authorize",
        {"redirect_uri": redirect_uri, "state": state, "email": email},
    )

    return get_auth(client)


def upload_file_and_wait(client, url, files):
    # upload jurisdictions
    resp = client.put(url, files=files)

    # wait for processing
    while True:
        time.sleep(2)
        file_status = json.loads(client.get(url).content)
        if file_status["processing"]["status"] == "PROCESSED":
            break


class JurisdictionAdmin(TaskSet):
    def setup(self):
        print("setting up: log in as audit admin and create an election")
        auth = do_login(self.client, "auditadmin", "ben@voting.works")

        # get organization ID
        self.org_id = auth["organizations"][0]["id"]
        self.audit_name = "LoadTest " + str(uuid.uuid4())

        # create election
        resp = self.client.post(
            "/election/new",
            data=json.dumps(
                {
                    "organizationId": self.org_id,
                    "auditName": self.audit_name,
                    "isMultiJurisdiction": True,
                }
            ),
            headers=JSON_HEADERS,
        )

        election_id = json.loads(resp.content)["electionId"]

        # get and set settings
        settings = json.loads(
            self.client.get(f"/election/{election_id}/settings").content
        )
        settings["state"] = "MI"
        self.client.put(
            f"/election/{election_id}/settings",
            data=json.dumps(settings),
            headers=JSON_HEADERS,
        )

        upload_file_and_wait(
            self.client,
            f"/election/{election_id}/jurisdiction/file",
            files={"jurisdictions": open(JURISDICTIONS_FILE, "rb")},
        )

        JurisdictionAdmin.election_id = election_id

    def on_start(self):
        try:
            self.email = JURISDICTIONS.pop()
        except:
            raise StopLocust()

        self.election_id = JurisdictionAdmin.election_id

        print(f"STARTING {self.email}")

        # log in
        auth = do_login(self.client, "jurisdictionadmin", self.email)

        # identify jurisdiction id
        for j in auth["jurisdictions"]:
            if j["election"]["id"] == self.election_id:
                self.jurisdiction_id = j["id"]
                break

        # upload manifest
        upload_file_and_wait(
            self.client,
            f"/election/{self.election_id}/jurisdiction/{self.jurisdiction_id}/ballot-manifest",
            files={"manifest": open(BIG_MANIFEST_FILE, "rb")},
        )

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
