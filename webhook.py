import json
import requests
###Designed for Slack, request json data accepts 'username' and 'text';
###   May need to be modified for other services.
def webhook(username, webhook_url, text):
    payload = {
      'username': username,
      'text': text
    }
    response = requests.post(
        webhook_url, data=json.dumps(payload),
        headers={'Content-Type': 'application/json'}
    )
    if response.status_code != 200:
        raise ValueError(
            'Request to slack returned an error %s, the response is:\n%s'
            % (response.status_code, response.text)
        )
