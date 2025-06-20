import csv
import os
import re
import threading
import time
import tkinter
from tkinter import ttk, messagebox
from tkinter import *
from datetime import datetime
from tkinter import messagebox as mess
import cv2
import numpy as np
from deepface.models.spoofing.FasNet import Fasnet

from classes.attendance import Attendances
from classes.employee import Employee
from model.classification_model import FacialRecognitionModel
from module import config, find, utils, database
# Initialize models
face_model = FacialRecognitionModel()
embedding_model = face_model.get_embedding_model()
anti_spoofing_model = Fasnet()

# Global variables for face processing
embedding_result = None
processing = False
face_bb = None
real_face = False
anti_face_conf = 0

def clear():
    """Clear the input fields for ID and Name, and reset the instruction message."""
    txt.delete(0, 'end')
    txt2.delete(0, 'end')
    res = "1)Take Images  ===> 2)Save Profile"
    message1.configure(text=res)

def validate_input(entry_id, entry_name):
    """
    Validate ID and Name inputs using regex patterns.

    Args:
        entry_id (str): Employee ID input
        entry_name (str): Employee name input

    Returns:
        bool: True if inputs are valid, False otherwise
    """
    id_pattern = r'^\d{1,3}$'
    name_pattern = r'^[a-zA-Z\s-]{1,50}$'

    id_value = entry_id.strip()
    name_value = entry_name.strip()

    # Validate ID
    if not id_value:
        messagebox.showerror("Error", "ID cannot be empty")
        return
    if not re.match(id_pattern, id_value):
        messagebox.showerror("Error", "ID must contain only numbers and be 1-3 digits long")
        return

    # Validate Name
    if not name_value:
        messagebox.showerror("Error", "Name cannot be empty")
        return
    if not re.match(name_pattern, name_value):
        messagebox.showerror("Error", "Name must contain only letters, spaces, or hyphens (max 50 characters)")
        return

    return True

def load_attendance_to_table(type_="checkin"):
    today = datetime.now().strftime("%Y-%m-%d")
    result = database.get_attendance_by_date(today)

    for item in tb.get_children():
        tb.delete(item)

    for row in result:
        emp_id = row[1]
        employee = database.get_employee_by_id(emp_id)
        name = employee.name if employee else "Unknown"
        date = row[2]
        checkin_time = row[3]
        checkout_time = row[4]
        if type_ == "checkin":
            tb.insert('', 'end', text=emp_id,values=(name, date, checkin_time))

        else:
            tb.insert('', 'end', text=emp_id,values=(name, date, checkout_time))

def async_preprocess(frame, embedding_model):
    """
    Preprocess a frame asynchronously to extract face embeddings and detect spoofing.

    Args:
        frame: Video frame to process
        embedding_model: Model for generating face embeddings
    """
    global embedding_result, processing, face_bb, real_face, anti_face_conf
    processing = True
    embedding_result, face_bb = utils.preprocess(frame, embedding_model)
    if face_bb is not None:
        facial_area = (face_bb.x, face_bb.y, face_bb.w, face_bb.h)
        real_face, anti_face_conf = anti_spoofing_model.analyze(frame, facial_area)
    processing = False

def check_id_exists(id_value, data_path):
    """
    Check if an employee ID already exists in the employee db.

    Args:
        id_value (str): Employee ID to check

    Returns:
        bool: True if ID exists, False otherwise
    """
    if not os.path.exists(config.EMPLOYEE_CSV):
        return False
    with open(data_path, 'r', newline='') as f:
        reader = csv.reader(f)
        next(reader, None)  # Skip header
        for row in reader:
            if row and row[0] == id_value:
                return True
    return False

def check_admin_account():
    """
    Check if admin credentials are set in the db.

    Returns:
        tuple: (admin_username, admin_password) if credentials exist, else None
    """
    username = entry_username.get().strip()
    password = entry_password.get().strip()

    admin = database.get_admin()
    if username == admin.username and password == admin.password:
        return True
    else:
        messagebox.showerror("Error", "Invalid admin credentials")
        return False

def change_password():
    """
    Change the admin password by verifying the current password and setting a new one.

    Validates inputs, checks current password, and updates the password in the db.
    """
    if not check_admin_account():
        messagebox.showerror("Error", "Invalid admin credentials")
        return

    old_pass.delete(0, 'end')
    new_pass.delete(0, 'end')
    confirm_pass.delete(0, 'end')

    change_pass_window.deiconify()
    change_pass_window.grab_set()

    def do_change_password():
        current_password = old_pass.get().strip()
        new_password_val = new_pass.get().strip()
        confirm_pass_val = confirm_pass.get().strip()

        # Đọc mật khẩu hiện tại từ file
        admin_username = "admin"
        admin_password = None
        if os.path.exists(config.ADMIN_DIR):
            with open(config.ADMIN_DIR, 'r') as f:
                lines = f.readlines()
                admin_password = lines[1].strip() if len(lines) > 1 else None
        if admin_password is None:
            messagebox.showerror("Error", "Admin password file is corrupted!")
            return

        if not current_password or not new_password_val or not confirm_pass_val:
            messagebox.showerror("Error", "All fields are required")
        elif current_password != admin_password:
            messagebox.showerror("Error", "Old password is incorrect")
        elif new_password_val != confirm_pass_val:
            messagebox.showerror("Error", "New passwords do not match")
        else:
            with open(config.ADMIN_DIR, 'w') as f:
                f.write(f"{admin_username}\n{new_password_val}\n")
            messagebox.showinfo("Success", "Password changed successfully")

        change_pass_window.withdraw()
        change_pass_window.grab_release()

    change_pass_window.verify_button.config(command=do_change_password)

def Save(name_value=None, img_path=None, embedding_path=None, id_value=None):
    """Verify admin credentials and save employee data if valid."""

    if check_admin_account():
        employee = Employee(name_value, img_path, embedding_path, int(id_value))
        database.create_employee(employee)
        messagebox.showinfo("Success", f"Saved profile for ID: {id_value}, Name: {name_value}")

        txt.delete(0, 'end')
        txt2.delete(0, 'end')

        entry_username.delete(0, 'end')
        entry_password.delete(0, 'end')

        admin_window.withdraw()
        admin_window.grab_release()
    else:
        messagebox.showerror("Error", "Invalid username or password")

def SaveProfile():
    """
    Save employee profile (ID, name, image path, and embedding) after admin verification.

    Validates inputs, checks for duplicate IDs, and saves data to db after admin authentication.
    """

    id_value = txt.get()
    name_value = txt2.get()
    img_path = os.path.join(config.EMPLOYEE_DIR, f"{id_value}.jpg")
    if not validate_input(id_value, name_value):
        return
    if not os.path.exists(img_path):
        messagebox.showerror("Error", f"Image for ID {id_value} does not exist. Please capture the image first.")
        return
    else:
        embedding_path = os.path.join(config.EMPLOYEE_EMBEDDING, f"{id_value}.npy")



    admin_window.verify_button.config(command=lambda: Save(name_value,img_path, embedding_path, id_value))
    admin_window.deiconify()
    admin_window.grab_set()

def TakeImages():
    """
    Capture an employee's face image using webcam and save it with embeddings.

    Validates inputs, checks for duplicate IDs, captures image on 's' key press,
    and saves both the image and its embedding.
    """

    id_value = txt.get()
    name_value = txt2.get()

    if validate_input(id_value, name_value) and not database.check_employee_exists(id_value):
        cap = cv2.VideoCapture(0)
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                print("Error capturing frame")
                break
            cv2.imshow("Webcam", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('s'):
                img_path = os.path.join(config.EMPLOYEE_DIR, f"{id_value}.jpg")
                cv2.imwrite(img_path, frame)
                print(f"Saved image: {img_path}")
                messagebox.showinfo("Success", f"Stored image path: {img_path}")

                embedding_img, _ = utils.preprocess(img_path, embedding_model)
                np.save(os.path.join(config.EMPLOYEE_EMBEDDING, f"{id_value}.npy"), embedding_img)
                break
            elif key == ord('q'):
                break
        cap.release()
        cv2.destroyAllWindows()
    elif not validate_input(id_value, name_value):
        messagebox.showerror("Error", "Invalid ID or Name")
    else:
        messagebox.showerror("Error", "ID already exists in database")

def Attendance(type_="checkin"):
    """
    Track and record employee attendance using face recognition.
    type_: "checkin" hoặc "checkout"
    """
    today = datetime.now()
    threshold = config.THRESHOLD

    # Chọn thư mục và tên cột theo loại điểm danh
    if type_ == "checkin":
        report_dir = config.ATTENDANCE_REPORT
        time_col = "checkin"
        success_msg = "Check in success."
    else:
        report_dir = config.CHECKOUT_REPORT
        time_col = "checkout"
        success_msg = "Checked out success."

    os.makedirs(report_dir, exist_ok=True)

    # Clear attendance table
    for item in tb.get_children():
        tb.delete(item)

    # Start video capture
    cap = cv2.VideoCapture(0)
    frame_id = 0
    frame_interval = 30

    start_time = time.time()
    time_out = 10

    while cap.isOpened():
        current_time = time.time()
        ret, frame = cap.read()
        if not ret:
            print(f"Error with frame {frame_id}")
            break
        frame_id += 1

        # Process frame periodically
        if frame_id % frame_interval == 0 and not processing:
            threading.Thread(target=async_preprocess, args=(frame.copy(), embedding_model)).start()

        # Verify and log attendance
        if embedding_result is not None and real_face:
            id, identity, distant = find.findPerson(embedding_result)
            scale = utils.distance_to_similarity(distant)

            if (current_time - start_time >= time_out/2):
                if identity == "unknown":
                    messagebox.showinfo("Error", "Unknown face detected!")
                    break
                if type_ == "checkin":
                    can_write = distant <= threshold and not database.check_id_attended_today(id)
                    if can_write:
                        attendance = Attendances(id, today.strftime("%Y-%m-%d"), today.strftime("%H:%M:%S"))
                        database.check_in(attendance)
                        database.check_late(attendance.employee_id,attendance.check_in)
                        load_attendance_to_table("checkin")
                        messagebox.showinfo("Success", success_msg)
                        break
                    else:
                        messagebox.showinfo("Error", "Employee has already checked in today")
                        break
                elif type_ == "checkout":
                    can_write = distant <= threshold and database.check_id_attended_today(id) and not database.check_id_out_today(id)
                    if can_write:
                        database.check_out(id,today.strftime("%Y-%m-%d"),today.strftime("%H:%M:%S"))
                        database.check_early(id, today.strftime("%H:%M:%S"))
                        load_attendance_to_table("checkout")
                        messagebox.showinfo("Success", success_msg)
                        break
                    else:
                        messagebox.showinfo("Error", "Employee has not checked in today or has already checked out")
                        break

            # Visualize results
            color = (0, 255, 0) if distant <= threshold else (0, 0, 255)
            cv2.putText(frame, f"Hello: {identity}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
            cv2.putText(frame, f"Match: {scale:.1f}%", (50, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
            if face_bb:
                cv2.rectangle(frame, (face_bb.x, face_bb.y), (face_bb.x + face_bb.w, face_bb.y + face_bb.h), color, 2)
            cv2.imshow("img", frame)
            if current_time - start_time > time_out:
                break

        elif embedding_result is not None and not real_face:
            color = (0, 0, 255)
            cv2.putText(frame, "Fake Face", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
            cv2.putText(frame, f"Match: {anti_face_conf:.1f}%", (50, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
            if face_bb:
                cv2.rectangle(frame, (face_bb.x, face_bb.y), (face_bb.x + face_bb.w, face_bb.y + face_bb.h), color, 2)
            cv2.imshow("img", frame)
            if (current_time - start_time >= time_out/2):
                messagebox.showinfo("Error", "Fake Face Detected!")
                break

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

def OpenAdminWindow():
    """
    Open the admin login window and set the command for the verify button.
    """
    admin_window.deiconify()
    admin_window.grab_set()

    def AdminWindow():
        if check_admin_account():
            admin_window.withdraw()
            admin_window.grab_release()

            txt.delete(0, 'end')
            txt2.delete(0, 'end')

            entry_username.delete(0, 'end')
            entry_password.delete(0, 'end')
            load_employee_data()
            load_attendance_data()
            load_violation_data()
            management_window.deiconify()
            management_window.grab_set()
        else:
            messagebox.showerror("Error", "Invalid username or password")

    # Set the command for the verify button
    admin_window.verify_button.config(command=AdminWindow)
def OpenEditWindow():
    selected = tree.focus()
    if not selected:
        messagebox.showwarning("Chọn dòng", "Vui lòng chọn một nhân viên để sửa.")
        return

    values = tree.item(selected, 'values')
    emp_id = values[0]

    edit_win = tkinter.Toplevel(management_window)
    edit_win.title(f"Chỉnh sửa nhân viên ID {emp_id}")
    edit_win.geometry("400x200")

    tkinter.Label(edit_win, text="Tên:").grid(row=0, column=0, padx=10, pady=5, sticky='e')
    entry_name = tkinter.Entry(edit_win)
    entry_name.insert(0, values[1])
    entry_name.grid(row=0, column=1, padx=10, pady=5, sticky='w')

    tkinter.Label(edit_win, text="Ảnh (đường dẫn):").grid(row=1, column=0, padx=10, pady=5, sticky='e')
    entry_img = tkinter.Entry(edit_win)
    entry_img.insert(0, values[2])
    entry_img.grid(row=1, column=1, padx=10, pady=5, sticky='w')

    tkinter.Label(edit_win, text="Embedding:").grid(row=2, column=0, padx=10, pady=5, sticky='e')
    entry_embed = tkinter.Entry(edit_win)
    entry_embed.insert(0, values[3])
    entry_embed.grid(row=2, column=1, padx=10, pady=5, sticky='w')

    btn_update = tkinter.Button(edit_win, text="Save", width=12,
                                command=lambda: database.update_employee(emp_id, entry_name.get(), entry_img.get(), entry_embed.get()))
    btn_update.grid(row=3, column=0, padx=10, pady=15)

    btn_delete = tkinter.Button(edit_win, text="Delete", width=12, command=None)
    btn_delete.grid(row=3, column=1, padx=10, pady=15)

def load_employee_data():
    """
    Load employee data from db and populate the Treeview.
    """
    try:
        # Clear existing data in the Treeview
        for item in tree.get_children():
            tree.delete(item)

        result = database.read_employees()
        for row in result:
            tree.insert('', 'end', values=(row[0], row[1], row[2], row[3]))
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load employee data: {e}")
        return

def load_attendance_data():
    """
    Load attendance from db and populate the Treeview.
    """
    # Clear existing data in the Treeview
    for item in attendance_tree.get_children():
        attendance_tree.delete(item)
    try:
        result = database.get_attendance_by_date(datetime.now().strftime("%Y-%m-%d"))
        for row in result:
            employee = database.get_employee_by_id(row[1])
            attendance_tree.insert('', 'end', values=(row[0], employee.name, row[2], row[3],row[4]))
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load attendance data: {e}")
        return

def load_violation_data():
    """
    Load violation data from db and populate the Treeview.
    """
    # Clear existing data in the Treeview
    for item in violation_tree.get_children():
        violation_tree.delete(item)
    try:
        result = database.get_violation_today()
        for violation in result:
            employee = database.get_employee_by_id(violation[1])
            policy = database.get_policy_by_id(violation[2])
            violation_tree.insert('', 'end', values=(violation[0], employee.name, policy.name,violation[3],violation[4],violation[5]))
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load violation data: {e}")
        return


# Front End
window = tkinter.Tk()
window.title("Face Recognition Based Attendance System")
window.geometry("1280x720")
window.resizable(True, True)
window.configure(background='#99ffcc')

# Admin Window
admin_window = tkinter.Toplevel(window)
admin_window.title("Đăng nhập Admin")
admin_window.geometry("300x300")
admin_window.withdraw()

tkinter.Label(admin_window, text="Username:", width=20, height=1, fg="black", bg="white", font=('times', 17, ' bold ')).pack(pady=10)
entry_username = tkinter.Entry(admin_window, width=32, fg="black", bg="#e1f2f2", highlightcolor="#00aeff", highlightthickness=3, font=('times', 15, ' bold '))
entry_username.pack()

tkinter.Label(admin_window, text="Password:", width=20, height=1, fg="black", bg="white", font=('times', 17, ' bold ')).pack(pady=10)
entry_password = tkinter.Entry(admin_window, width=32, fg="black", bg="#e1f2f2", highlightcolor="#00aeff", highlightthickness=3, font=('times', 15, ' bold '),show= ".")
entry_password.pack()

# Create verify button without assigning command immediately
admin_window.verify_button = tkinter.Button(admin_window, text="Xác nhận")
admin_window.verify_button.pack(pady=20)

change_pass_btn = tkinter.Button(admin_window, text="Đổi mật khẩu",command=change_password)
change_pass_btn.pack(pady=5)

# Change Password Window
change_pass_window = tkinter.Toplevel(admin_window)
change_pass_window.title("Đổi mật khẩu Admin")
change_pass_window.geometry("300x300")
change_pass_window.withdraw()

tkinter.Label(change_pass_window, text="Old Password:", width=20, height=1, fg="black", bg="white", font=('times', 17, ' bold ')).pack(pady=10)
old_pass = tkinter.Entry(change_pass_window, width=32, fg="black", bg="#e1f2f2", highlightcolor="#00aeff", highlightthickness=3, font=('times', 15, ' bold '))
old_pass.pack()

tkinter.Label(change_pass_window, text="New Password:", width=20, height=1, fg="black", bg="white", font=('times', 17, ' bold ')).pack(pady=10)
new_pass = tkinter.Entry(change_pass_window, width=32, fg="black", bg="#e1f2f2", highlightcolor="#00aeff", highlightthickness=3, font=('times', 15, ' bold '))
new_pass.pack()

tkinter.Label(change_pass_window, text="Confirm Password:", width=20, height=1, fg="black", bg="white", font=('times', 17, ' bold ')).pack(pady=10)
confirm_pass = tkinter.Entry(change_pass_window, width=32, fg="black", bg="#e1f2f2", highlightcolor="#00aeff", highlightthickness=3, font=('times', 15, ' bold '))
confirm_pass.pack()

change_pass_window.verify_button = tkinter.Button(change_pass_window, text="Xác nhận")
change_pass_window.verify_button.pack(pady=20)

# Management Window
management_window = tkinter.Tk()
management_window.title("Management Window")
management_window.geometry("800x450")
management_window.resizable(True, True)
management_window.configure(background='#99ffcc')
management_window.withdraw()  # Start hidden

notebook = ttk.Notebook(management_window)
notebook.pack(fill='both', expand=True)

tab_employee = ttk.Frame(notebook)
notebook.add(tab_employee, text='Quản lý nhân viên')
tab_attendance = ttk.Frame(notebook)
notebook.add(tab_attendance, text='Chấm công hôm nay')
violation_tab = ttk.Frame(notebook)
notebook.add(violation_tab, text="Vi phạm hôm nay")

lbl_nv = ttk.Label(tab_employee, text="Danh sách nhân viên", font=('Arial', 14))
lbl_nv.pack(pady=10)

columns = ("id", "name", "img", "embedding")
tree = ttk.Treeview(tab_employee, columns=columns, show="headings", height=10)

tree.heading("id", text="ID_NV")
tree.heading("name", text="Tên")
tree.heading("img", text="Ảnh (đường dẫn)")
tree.heading("embedding", text="Embedding")

tree.column("id", width=50)
tree.column("name", width=150)
tree.column("img", width=200)
tree.column("embedding", width=400)
tree.pack(pady=10)

btn_edit = ttk.Button(tab_employee, text="Edit", command=OpenEditWindow)
btn_edit.pack(pady=10)

lbl_cc = ttk.Label(tab_attendance, text="Chấm công nhân viên", font=('Arial', 14))
lbl_cc.pack(pady=10)
columns_attendance = ("id", "name", "date", "checkin","checkout")
attendance_tree = ttk.Treeview(tab_attendance, columns=columns_attendance, show="headings", height=10)

attendance_tree.heading("id", text="ID_TG")
attendance_tree.heading("name", text="Tên")
attendance_tree.heading("date", text="Ngày")
attendance_tree.heading("checkin", text="Checkin")
attendance_tree.heading("checkout", text="Checkout")

attendance_tree.column("id", width=50)
attendance_tree.column("name", width=150)
attendance_tree.column("date", width=100)
attendance_tree.column("checkin", width=100)
attendance_tree.column("checkout", width=100)
attendance_tree.pack(pady=10)

columns_violation = ("id", "name","type","minutes", "deduction","date")
violation_tree = ttk.Treeview(violation_tab, columns=columns_violation, show="headings")
violation_tree.heading("id", text="ID_VP")
violation_tree.heading("name", text="Tên người vi phạm")
violation_tree.heading("type", text="Loại vi phạm")
violation_tree.heading("minutes", text="Số phút vi phạm")
violation_tree.heading("deduction", text="Số tiền phạt")
violation_tree.heading("date", text="Ngày vi phạm")
violation_tree.pack(fill="both", expand=True)

violation_tree.column("id", width=50)
violation_tree.column("name", width=150)
violation_tree.column("type", width=100)
violation_tree.column("minutes", width=100)
violation_tree.column("deduction", width=100)
violation_tree.column("date", width=100)

quit_btn = tkinter.Button(management_window, text="Quit", fg="black", bg="#ff4d4d", width=17, height=1, activebackground="white", font=('times', 16, ' bold '), command=management_window.withdraw)
quit_btn.pack(pady=10)

# Help menubar
menubar = Menu(window)
help_menu = Menu(menubar, tearoff=0)
help_menu.add_command(label="Change Password!")
help_menu.add_command(label="Contact Us")
help_menu.add_separator()
help_menu.add_command(label="Exit")
menubar.add_cascade(label="Help", menu=help_menu)

# Add ABOUT label to menubar
menubar.add_command(label="About")

# Attach menu to window
window.config(menu=menubar)

# Main window
message3 = tkinter.Label(window, text="Face Recognition Based Attendance System", fg="white", bg="#355454", width=60, height=1, font=('times', 29, ' bold '))
message3.place(x=10, y=10, relwidth=1)

# Frames
frame1 = tkinter.Frame(window, bg="white")
frame1.place(relx=0.11, rely=0.15, relwidth=0.39, relheight=0.80)

frame2 = tkinter.Frame(window, bg="white")
frame2.place(relx=0.51, rely=0.15, relwidth=0.39, relheight=0.80)

# Frame headers
fr_head1 = tkinter.Label(frame1, text="Register New Employee", fg="white", bg="black", font=('times', 17, ' bold '))
fr_head1.place(x=0, y=0, relwidth=1)

fr_head2 = tkinter.Label(frame2, text="Mark Employee's attendance", fg="white", bg="black", font=('times', 17, ' bold '))
fr_head2.place(x=0, y=0, relwidth=1)

# Registration frame
lbl = tkinter.Label(frame1, text="Enter ID", width=20, height=1, fg="black", bg="white", font=('times', 17, ' bold '))
lbl.place(x=0, y=55)

txt = tkinter.Entry(frame1, width=32, fg="black", bg="#e1f2f2", highlightcolor="#00aeff", highlightthickness=3, font=('times', 15, ' bold '))
txt.place(x=55, y=88, relwidth=0.75)

lbl2 = tkinter.Label(frame1, text="Enter Name", width=20, fg="black", bg="white", font=('times', 17, ' bold '))
lbl2.place(x=0, y=140)

txt2 = tkinter.Entry(frame1, width=32, fg="black", bg="#e1f2f2", highlightcolor="#00aeff", highlightthickness=3, font=('times', 15, ' bold '))
txt2.place(x=55, y=173, relwidth=0.75)

message0 = tkinter.Label(frame1, text="Follow the steps...", bg="white", fg="black", width=39, height=1, font=('times', 16, ' bold '))
message0.place(x=7, y=275)

message1 = tkinter.Label(frame1, text="1)Take Images  ===> 2)Save Profile", bg="white", fg="black", width=39, height=1, activebackground="yellow", font=('times', 15, ' bold '))
message1.place(x=7, y=300)

message = tkinter.Label(frame1, text="", bg="white", fg="black", width=39, height=1, activebackground="yellow", font=('times', 16, ' bold '))
message.place(x=7, y=500)

# Attendance frame
lbl3 = tkinter.Label(frame2, text="Attendance Table", width=20, fg="black", bg="white", height=1, font=('times', 17, ' bold '))
lbl3.place(x=100, y=115)

# Buttons
clearButton = tkinter.Button(frame1, text="Clear", command=clear, fg="white", bg="#13059c", width=11, activebackground="white", font=('times', 12, ' bold '))
clearButton.place(x=55, y=230, relwidth=0.29)

takeImg = tkinter.Button(frame1, text="Take Images", command=TakeImages, fg="black", bg="#00aeff", width=34, height=1, activebackground="white", font=('times', 16, ' bold '))
takeImg.place(x=30, y=350, relwidth=0.89)

trainImg = tkinter.Button(frame1, text="Save Profile", fg="black", command=SaveProfile, bg="#00aeff", width=17, height=1, activebackground="white", font=('times', 16, ' bold '))
trainImg.place(x=30, y=430)

manageBtn = tkinter.Button(frame1, text="Manage", fg="black", bg="#00aeff",command=OpenAdminWindow ,width=17, height=1, activebackground="white", font=('times', 16, ' bold '))
manageBtn.place(x=270, y=430)

trackImg = tkinter.Button(frame2, text="Checkin", command=lambda: Attendance("checkin"), fg="black", bg="#00aeff", height=1, activebackground="white", font=('times', 16, ' bold '))
trackImg.place(x=30, y=60, relwidth=0.44)

checkoutBtn = tkinter.Button(frame2, text="Checkout", command=lambda: Attendance("checkout"), fg="black", bg="#00aeff", height=1, activebackground="white", font=('times', 16, ' bold '))
checkoutBtn.place(relx=0.52, x=0, y=60, relwidth=0.44)

quitWindow = tkinter.Button(frame2, text="Quit", command= lambda: (window.destroy(),management_window.destroy()), fg="white", bg="#13059c", width=35, height=1, activebackground="white", font=('times', 16, ' bold '))
quitWindow.place(x=30, y=450, relwidth=0.89)

# Attendance table
style = ttk.Style()
style.configure("mystyle.Treeview", highlightthickness=0, bd=0, font=('Calibri', 11))  # Modify the font of the body
style.configure("mystyle.Treeview.Heading", font=('times', 13, 'bold'))  # Modify the font of the headings
style.layout("mystyle.Treeview", [('mystyle.Treeview.treearea', {'sticky': 'nswe'})])  # Remove the borders
tb = ttk.Treeview(frame2, height=13, columns=('name', 'date', 'checkin','checkout'), style="mystyle.Treeview")
tb.column('#0', width=82)
tb.column('name', width=130)
tb.column('date', width=133)
tb.column('checkin', width=133)
tb.grid(row=2, column=0, padx=(0, 0), pady=(150, 0), columnspan=4)
tb.heading('#0', text='ID')
tb.heading('name', text='NAME')
tb.heading('date', text='DATE')
tb.heading('checkin', text='TIME')

# Scrollbar
scroll = ttk.Scrollbar(frame2, orient='vertical', command=tb.yview)
scroll.grid(row=2, column=4, padx=(0, 100), pady=(150, 0), sticky='ns')
tb.configure(yscrollcommand=scroll.set)

# Closing lines
window.protocol("WM_DELETE_WINDOW")
window.mainloop()