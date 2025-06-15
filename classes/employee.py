
class Employee:
    def __init__(self, name: str, img: str, embedding: str, id: int = None):

        self.id = id
        self.name = name
        self.img = img
        self.embedding = embedding

    def get_details(self) -> str:
        return f"ID: {self.id}, Name: {self.name}, Image: {self.img}, Embedding: {self.embedding}"
