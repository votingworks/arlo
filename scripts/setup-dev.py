# pylint: disable=invalid-name
import sys
import os
import signal
import subprocess

children = []

try:
    owd = os.getcwd()

    d = ''
    noAuthPath = ''

    print('Running script to setup local Arlo instance...')

    res = input('Do you have an instance of nOAuth installed? [y/N]')

    if res != 'y':
        res = input('Would you like to install nOAuth? [Y/n]')

        if res == 'n':
            print('Please install nOAuth instance before running this script again.')
            sys.exit(0)

        d = input('Where would you like nOAuth installed? [default: .]')

        if not d:
            d = '.'

        d = os.path.expanduser(d)

        if not os.path.exists(d):
            os.makedirs(d)

        os.chdir(d)

        command = 'git clone https://github.com/votingworks/nOAuth.git'

        subprocess.run([command], shell=True, check=True)

        noAuthPath = d

    while True:
        if not noAuthPath:
            d = input('Where is nOAuth located?')

        d = os.path.expanduser(d)
        if os.path.exists(d):
            noAuthPath = d
            break

        print('That path does not exist.')
        d = ''

    os.chdir(noAuthPath)

    res = input('Would you like to run nOAuth? [Y/n]')
    if res == 'n':
        print('Please see README for running Arlo with custom nOAuth.')
        sys.exit(0)

    port = ''
    while True:
        res = input('What port should nOAuth be run on? [8080]')

        if not res:
            res = '8080'

        try:
            int(res)
            port = res
            break
        except ValueError:
            print('"{}" is not a valid port.'.format(res))

    print('Running nOAuth on port {}'.format(res))
    command = 'PORT=8080 pipenv run python app.py'
    child = subprocess.Popen([command], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid) # pylint: disable=subprocess-popen-preexec-fn


    children.append(child)

    res = input('Would you like to install the Arlo dev environment? [y/N]')

    if res == 'y':
        subprocess.run(['make dev-environment'], check=True)

    orgname = input('What is the name of your test organization? [test]')

    if not orgname:
        orgname = 'test'

    os.chdir(owd)

    print('Setting up test org')
    output = subprocess.run(['pipenv run python -m scripts.create-org {}'.format(orgname)], shell=True, capture_output=True, text=True, check=True)

    orgid = output.stdout.strip()
    print(orgid)



    email = input('What is the email for the audit administrator? [test@test.test]')

    if not email:
        email = 'test@test.test'

    subprocess.run(['pipenv run python -m scripts.create-admin {} {}'.format(orgid, email)], shell=True, check=True)



    print('Configuring arlo environment')
    os.environ['ARLO_AUDITADMIN_AUTH0_BASE_URL'] = 'http://localhost:{}'.format(port)
    os.environ['ARLO_JURISDICTIONADMIN_AUTH0_BASE_URL'] = 'http://localhost:{}'.format(port)


    os.environ['ARLO_AUDITADMIN_AUTH0_CLIENT_ID'] = 'test'
    os.environ['ARLO_JURISDICTIONADMIN_AUTH0_CLIENT_ID'] = 'test'

    os.environ['ARLO_AUDITADMIN_AUTH0_CLIENT_SECRET'] = 'secret'
    os.environ['ARLO_JURISDICTIONADMIN_AUTH0_CLIENT_SECRET'] = 'secret'


    print('Running Arlo. Happy auditing!')
    subprocess.run(['./run-dev.sh'], check=True)



finally:
    # Clean up
    for child in children:
        os.killpg(os.getpgid(child.pid), signal.SIGTERM)


    os.chdir(owd)
