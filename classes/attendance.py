
class Attendances:
    def __init__(self, employee_id: int, date: str, check_in: str, check_out: str = None, id: int = None):
        self.id = id
        self.employee_id = employee_id
        self.date = date
        self.check_in = check_in
        self.check_out = check_out

    def get_details(self) -> str:
        return f"ID: {self.id}, Employee ID: {self.employee_id}, Date: {self.date}, Check In: {self.check_in}, Check Out: {self.check_out}"
