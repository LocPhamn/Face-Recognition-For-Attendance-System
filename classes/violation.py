
class Violation:
    def __init__(self, employee_id: int,policy_id:int,late_minutes:int,deduction:int,date:str, id: int = None):
        self.id = id
        self.employee_id = employee_id
        self.id_policy = policy_id
        self.late_minutes = late_minutes
        self.deduction = deduction
        self.date = date

    def get_details(self) -> str:
        return f"ID: {self.id}, Employee ID: {self.employee_id}, Policy ID: {self.id_policy}, Type: {self.type}, Late Minutes: {self.late_minutes}, Deduction: {self.deduction}, Date: {self.date}"