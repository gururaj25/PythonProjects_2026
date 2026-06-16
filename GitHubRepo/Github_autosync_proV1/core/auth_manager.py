import keyring

SERVICE_NAME = "GitHubAutoSync"

class AuthManager:

    def save_token(self, username, token):
        keyring.set_password(SERVICE_NAME, username, token)

    def get_token(self, username):
        return keyring.get_password(SERVICE_NAME, username)