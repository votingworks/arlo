# pylint: disable=invalid-name
import sys
import os
import signal
import subprocess

children = []

try:
    owd = os.getcwd()

    d = ""
    noAuthPath = ""

    print("Running script to setup local Arlo instance...")
    print()

    print(
        "If this is your first time running Arlo, we recommend that you answer\n"
        + "no to the following question and follow the steps to use VotingWorks'\n"
        + "instance of nOAuth.\n"
    )

    res = input("Do you have an instance of nOAuth configured? [y/N]:")

    if res != "y":

        res = input("Would you like to use VotingWorks' instance of nOAuth? [Y/n]")

        if not res:
            res = "y"

        nOAuthAddr = "https://votingworks-noauth.herokuapp.com"
        if res not in ["Y", "y"]:

            res = input("Would you like to install nOAuth? [Y/n]")

            if res == "n":
                print(
                    "Please install nOAuth instance before running this script again."
                )
                sys.exit(0)

            d = input("Where would you like nOAuth installed? [default: .]")

            if not d:
                d = "."

            d = os.path.expanduser(d)

            if not os.path.exists(d):
                os.makedirs(d)

            os.chdir(d)

            command = "git clone https://github.com/votingworks/nOAuth.git"

            subprocess.run([command], shell=True, check=True)

            noAuthPath = d

            while True:
                if not noAuthPath:
                    d = input("Where is nOAuth located?")

                d = os.path.expanduser(d)
                if os.path.exists(d):
                    noAuthPath = d
                    break

                print("That path does not exist.")
                d = ""

            os.chdir(noAuthPath)

            res = input("Would you like to run nOAuth? [Y/n]")
            if res == "n":
                print("Please see README for running Arlo with custom nOAuth.")
                sys.exit(0)

            port = ""
            while True:
                res = input("What port should nOAuth be run on? [8080]")

                if not res:
                    res = "8080"

                try:
                    int(res)
                    port = res
                    break
                except ValueError:
                    print('"{}" is not a valid port.'.format(res))

            print("Running nOAuth on port {}".format(res))
            command = "PORT=8080 poetry run python app.py"
            # pylint: disable=subprocess-popen-preexec-fn
            child = subprocess.Popen(
                [command],
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid,
            )

            children.append(child)
            nOAuthAddr = "http://localhost:{}".format(port)

    print("Configuring arlo environment")
    os.environ["ARLO_AUDITADMIN_AUTH0_BASE_URL"] = nOAuthAddr
    os.environ["ARLO_JURISDICTIONADMIN_AUTH0_BASE_URL"] = nOAuthAddr

    os.environ["ARLO_AUDITADMIN_AUTH0_CLIENT_ID"] = "test"
    os.environ["ARLO_JURISDICTIONADMIN_AUTH0_CLIENT_ID"] = "test"

    os.environ["ARLO_AUDITADMIN_AUTH0_CLIENT_SECRET"] = "secret"
    os.environ["ARLO_JURISDICTIONADMIN_AUTH0_CLIENT_SECRET"] = "secret"

    os.environ["ARLO_SESSION_SECRET"] = "secret"
    os.environ["ARLO_HTTP_ORIGIN"] = "http://localhost:3000"

    res = input(
        "Would you like to install the Arlo dev environment?\n"
        + "If this is your first run of Arlo after download, you should do this. [y/N]"
    )

    if res == "y":
        subprocess.run(["make dev-environment"], check=True, shell=True)

    print("Migrating the database to the newest data model")
    subprocess.run(["alembic upgrade head"], check=True, shell=True)

    orgname = input("What is the name of your test organization? [test]")

    if not orgname:
        orgname = "test"

    os.chdir(owd)

    print("Setting up test org")
    output = subprocess.run(
        ["poetry run python -m scripts.create-org {}".format(orgname)],
        shell=True,
        capture_output=True,
        text=True,
        check=True,
    )

    orgid = output.stdout.strip()

    email = input("What is the email for the audit administrator? [test@test.test]")

    if not email:
        email = "test@test.test"

    subprocess.run(
        ["poetry run python -m scripts.create-admin {} {}".format(orgid, email)],
        shell=True,
        check=True,
    )

    print("Running Arlo. Happy auditing!")
    subprocess.run(["./run-dev.sh"], check=True)


finally:
    # Clean up
    for child in children:
        os.killpg(os.getpgid(child.pid), signal.SIGTERM)

    os.chdir(owd)
