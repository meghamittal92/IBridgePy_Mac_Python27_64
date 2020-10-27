import requests


def refresh_token(refreshToken, client_id):
    resp = requests.post('https://api.tdameritrade.com/v1/oauth2/token',
                         headers={'Content-Type': 'application/x-www-form-urlencoded'},
                         data={'grant_type': 'refresh_token',
                               'refresh_token': refreshToken,
                               'client_id': client_id})
    if resp.status_code != 200:
        print(__name__ + '__init__::refresh_token: EXIT, error=%s' % (resp.content,))
        print('Hint: 1. Check if apikey is correct in settings.py. Refer to this tutorial https://youtu.be/l3qBYMN4yMs')
        print('Hint: 2. Check if refreshToken is correct in settings.py. It is pretty long, and should be url decoded.')
        print('Hint: 3: Refresh token is valid up to 90 days. Create a new refresh token when needed. https://youtu.be/Ql6VnR0GIYY')
        raise Exception('Could not authenticate!')
    return resp.json()
