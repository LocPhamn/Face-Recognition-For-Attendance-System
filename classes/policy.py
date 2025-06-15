
class Policy:
    def __init__(self, name:str, amount: int, hours: str, id:int = None):
        self.id = id
        self.name = name
        self.amount = amount
        self.hours = hours

    def get_details(self) -> str:
        return f"ID: {self.id}, Name: {self.name}, Amount: {self.amount}, Hours: {self.hours}"