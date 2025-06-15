from datetime import datetime

import mysql.connector
from classes import employee, attendance, violation
from classes.admin import Admin
from classes.employee import Employee
from classes.policy import Policy
from classes.violation import Violation


# Tạo kết nối
def connect_db():
    try:
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="Locpro@1997",
            database="attendance_db"
        )
    except mysql.connector.Error as err:
        print(f"Lỗi: {err}")

def create_employee(employee: employee.Employee):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO employee (employee_id, name, img, embedding) VALUES (%s,%s, %s, %s)",
        (employee.id,employee.name, employee.img, employee.embedding)
    )
    conn.commit()
    print("✅ Đã thêm nhân viên.")
    cursor.close()
    conn.close()

def read_employees():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM employee")
    result = cursor.fetchall()
    return result

def get_employee_by_id(emp_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM employee WHERE employee_id = %s", (emp_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    if result is None:
        print("Không tìm thấy nhân viên với ID:", emp_id)

    employee_data = Employee(result[1], result[2], result[3], result[0])
    return employee_data

# UPDATE - Cập nhật thông tin nhân viên
def update_employee(emp_id, name=None, img=None, embedding=None):
    conn = connect_db()
    cursor = conn.cursor()
    fields = []
    values = []

    if name:
        fields.append("name = %s")
        values.append(name)
    if img:
        fields.append("img = %s")
        values.append(img)
    if embedding is not None:
        fields.append("embedding = %s")
        values.append(embedding)

    values.append(emp_id)
    sql = f"UPDATE employee SET {', '.join(fields)} WHERE employee_id = %s"
    cursor.execute(sql, values)
    conn.commit()
    print("✅ Đã cập nhật.")
    cursor.close()
    conn.close()

# DELETE - Xoá nhân viên
def delete_employee(emp_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM employee WHERE employee_id = %s", (emp_id,))
    conn.commit()
    print("✅ Đã xoá nhân viên.")
    cursor.close()
    conn.close()

def check_employee_exists(emp_id):
    """
    Kiểm tra xem nhân viên với emp_id có tồn tại trong cơ sở dữ liệu hay không.
    Trả về True nếu tồn tại, False nếu không.
    """
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM employee WHERE employee_id = %s", (emp_id,))
    result = cursor.fetchone()
    print("✅ Đã kiểm tra nhân viên.")
    cursor.close()
    conn.close()
    print("Thông tin nhân viên:", result[0])
    return result[0] > 0

# Attendance database interaction
def get_attendance_by_date(date):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM attendance WHERE date = %s", (date,))
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result

def check_id_attended_today(emp_id):
    """
    Kiểm tra xem nhân viên với emp_id đã điểm danh hôm nay chưa.
    Trả về True nếu đã điểm danh, False nếu chưa.
    """
    if emp_id is None:
        print("ID nhân viên không hợp lệ.")
        return False
    conn = connect_db()
    cursor = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    sql = "SELECT COUNT(*) FROM attendance WHERE employee_id = %s AND date = %s"
    cursor.execute(sql, (emp_id, today))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result[0] > 0

def check_in(attendance: attendance.Attendances):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO attendance (employee_id, date, checkin) VALUES (%s, %s, %s)",
        (attendance.employee_id, attendance.date, attendance.check_in)
    )
    conn.commit()
    print("✅ Đã thêm thông tin điểm danh.")
    cursor.close()
    conn.close()

def check_out(emp_id, date, time):
    """
    Điểm danh ra cho nhân viên với emp_id vào ngày date và thời gian time.
    """
    conn = connect_db()
    cursor = conn.cursor()
    sql = "UPDATE attendance SET checkout = %s WHERE employee_id = %s AND date = %s"
    cursor.execute(sql, (time, emp_id, date))
    conn.commit()
    cursor.close()
    conn.close()

def check_id_out_today(emp_id):
    """
    Kiểm tra xem nhân viên với emp_id đã điểm danh ra hôm nay chưa.
    Trả về True nếu đã điểm danh ra, False nếu chưa.
    """
    if emp_id is None:
        print("ID nhân viên không hợp lệ.")
        return False
    conn = connect_db()
    cursor = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    sql = "SELECT COUNT(*) FROM attendance WHERE employee_id = %s AND date = %s AND checkout IS NOT NULL"
    cursor.execute(sql, (emp_id, today))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result[0] > 0

# Admin database interaction

def get_admin():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM admin")
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    if result:
        return Admin(result[1],result[2])

# Violations database interaction

def check_late(emp_id,check_in_time):
    print(emp_id)
    today= datetime.now().strftime("%Y-%m-%d")
    con = connect_db()
    cursor = con.cursor()
    cursor.execute("SELECT * FROM policy WHERE hours < %s", (check_in_time,))
    result = cursor.fetchone()
    policy = Policy(result[1], result[2], result[3], result[0]) if result else None
    if policy:
        check_in_time = datetime.strptime(check_in_time, "%H:%M:%S")
        policy_hours = datetime.strptime(str(policy.hours), "%H:%M:%S")
        late_minutes = (check_in_time - policy_hours).total_seconds() / 60
        deduction = policy.amount * late_minutes
        date = today
        cursor.execute( "INSERT INTO violation (employee_id, policy_id, late_minutes, deduction, date) VALUES (%s, %s, %s, %s, %s)", params=(emp_id, policy.id, late_minutes, deduction, date))
        con.commit()
        print("✅ Đã thêm vi phạm.")
        cursor.close()

def check_early(emp_id,check_out_time):

    today= datetime.now().strftime("%Y-%m-%d")
    con = connect_db()
    cursor = con.cursor()
    cursor.execute("SELECT * FROM policy WHERE hours > %s", (check_out_time,))
    result = cursor.fetchone()
    policy = Policy(result[1], result[2], result[3], result[0]) if result else None
    if policy:
        check_out_time = datetime.strptime(check_out_time, "%H:%M:%S")
        policy_hours = datetime.strptime(policy.hours, "%H:%M:%S")
        late_minutes = (policy_hours - check_out_time).total_seconds() / 60
        deduction = policy.amount * late_minutes
        date = today
        cursor.execute( "INSERT INTO violation (employee_id, policy_id, late_minutes, deduction, date) VALUES (%s, %s, %s, %s, %s)", params=(emp_id, policy.id, late_minutes, deduction, date))
        con.commit()
        print("✅ Đã thêm vi phạm.")
        cursor.close()


def get_violation_today():
    conn = connect_db()
    cursor = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("SELECT * FROM violation WHERE date = %s", (today,))
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result

# Policy database interaction

def get_all_policies():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM policy")
    result = cursor.fetchall()
    policies = []
    for row in result:
        # Giả sử thứ tự cột là: id, name, amount, hours
        policy = Policy(
            name=row[1],
            amount=row[2],
            hours=row[3],
            id=row[0]
        )
        policies.append(policy)
    cursor.close()
    conn.close()
    return policies

def get_policy_by_id(policy_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM policy WHERE policy_id = %s", (policy_id,))
    result = cursor.fetchone()
    return Policy(
        name=result[1],
        amount=result[2],
        hours=result[3],
        id=result[0]
    ) if result else None
