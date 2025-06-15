
class Admin:
    def __init__(self, username, password):
        self.username = username
        self.password = password

    def get_details(self) -> str:
        return f"Username: {self.username}, Password: {self.passord}"