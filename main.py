import hmac
import os
import subprocess
from pathlib import Path
import requests

from dotenv import load_dotenv
from flask import Flask
from flask import request
import git
from ai_api_utils import generate_gemini_text
import pamji_bot
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / '.env')


app = Flask(__name__)
API_NAME = os.getenv('API_NAME')
API_DESCRIPTION = os.getenv('API_DESCRIPTION')
API_VERSION = os.getenv('API_VERSION')
DEPLOY_COMMAND = os.getenv('DEPLOY_COMMAND')
GITHUB_WEBHOOK_SECRET = os.getenv('GITHUB_WEBHOOK_SECRET')


def verify_signature():
    header_signature = request.headers.get('X-Hub-Signature-256')

    if not header_signature:
        return False

    sha_name, signature = header_signature.split('=')
    if sha_name != 'sha256':
        return False

    local_signature = hmac.new(GITHUB_WEBHOOK_SECRET.encode(), msg=request.get_data(), digestmod='sha256')
    return hmac.compare_digest(local_signature.hexdigest(), signature)


@app.route('/github-webhook', methods=['POST'])
def github_webhook():
    print(request.data)
    print(request.json)
    resp=request.json
    ref=resp['ref']
    before=resp['before']
    after=resp['after']
    owner=resp['repository']['owner']['name']
    url=resp['repository']["html_url"]
    description=resp['repository']['description']
    push_time=resp['repository']['updated_at']
    pusher=resp['pusher']['name']
    comit_description=resp["head_commit"]["message"]
    commit_url=resp["commits"][0]["url"]
    repo=resp["repository"]["name"]  
    dif_url=commit_url+".diff"
    url="https://github.com/pam-ji/github-bot/commit/b3bbfc779831200522549c41a082a0dbab12d1e3.diff"
    response = requests.get(url)
    if response.status_code == 200:
        diff = response.text
        print(diff)
    else:
        print("Fehler:", response.status_code)
    prompt=response.text
    instructions="You are the github review bot. The ouput text needs to be in markdown format. highlight the important changes in the changes section. Output a maximum of 5 Lines for unimportant changes in the changes section. For important changes you can use a maximum of 10 lines changes in the changes section. Only give personal oppinion within the Copilot Advisery section if the changes are insecure, buggy, or shitcode."
    max_tokens=256
    review=generate_gemini_text(prompt, instructions, max_tokens)
    print(review)


@app.route('/')
def index():
    return {
        'name': API_NAME,
        'description': API_DESCRIPTION,
        'version': API_VERSION,
    }


@app.route('/deploy', methods=['POST'])
def deploy():
    verified = verify_signature()

    if not verified:
        return {
            'message': 'The request could not be verified. Signature missing or does not match.',
            'verified': False,
        }, 400

    subprocess.call(DEPLOY_COMMAND, shell=True)

    return {
        'message': 'Deploying...',
        'verified': True,
    }
repo='https://github.com/pam-ji/github-bot'
comit_id="b3bbfc779831200522549c41a082a0dbab12d1e3"
def get_commit_diff(repo, commit_id):
    repo=git.Repo(repo)
    commit = repo.commit(commit_id)
    response = requests.get(url)
    if response.status_code == 200:
        diff = response.text
        print(diff)
    else:
        print("Fehler:", response.status_code)

    # Erhalte die Änderungen des Commits
    diff = commit.diff()

    # Durchlaufe die Änderungen
    for diff_file in diff:
        # Erhalte den Dateinamen und den Änderungstyp
        filename = diff_file.a_path
        change_type = diff_file.change_type

        # Erhalte den Inhalt der Datei vor und nach dem Commit
        old_content = diff_file.a_blob.data_stream.read().decode('utf-8')
        new_content = diff_file.b_blob.data_stream.read().decode('utf-8')

        # Durchlaufe die Zeilen der Datei und erhalte die Änderungen
        for line in diff_file.diff.decode('utf-8').splitlines():
            # Erhalte den Änderungstyp (z.B. '+', '-', ' ')
            change_type_line = line[0]

            # Erhalte den Text der Zeile
            line_text = line[1:]

            # Verarbeite die Änderung
            if change_type_line == '+':
                print(f'Added line: {line_text}')
            elif change_type_line == '-':
                print(f'Removed line: {line_text}')
            else:
                print(f'Unchanged line: {line_text}')



if __name__ == '__main__':
    app.run()
    # url="https://github.com/pam-ji/github-bot/commit/b3bbfc779831200522549c41a082a0dbab12d1e3.diff"
    # response = requests.get(url)
    # if response.status_code == 200:
    #     diff = response.text
    #     print(diff)
    # else:
    #     print("Fehler:", response.status_code)
    # prompt=response.text
    # instructions="You are the github review bot. The ouput text needs to be in markdown format. highlight the important changes in the changes section. Output a maximum of 5 Lines for unimportant changes in the changes section. For important changes you can use a maximum of 10 lines changes in the changes section. Only give personal oppinion within the Copilot Advisery section if the changes are insecure, buggy, or shitcode."
    # max_tokens=256
    # review=generate_gemini_text(prompt, instructions, max_tokens)
    # print(review)