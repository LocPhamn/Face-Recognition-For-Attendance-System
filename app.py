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
from model.classification_model import FacialRecognitionModel
from module import config, find, utils

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

def load_attendance_to_table(data_path):
    """
    Load today's attendance data from CSV and display in the attendance table.

    Displays error if the CSV file for the current date does not exist.
    """
    today = datetime.now().strftime("%Y-%m-%d")
    csv_filepath = os.path.join(data_path, f"{today}.csv")

    if not os.path.exists(csv_filepath):
        messagebox.showerror("Error", f"Attendance file {today}.csv not found")
        return

    with open(csv_filepath, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        for row in reader:
            if len(row) == 4:
                tb.insert('', 'end', text=row[0], values=(row[1], row[2], row[3]))

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
    Check if an employee ID already exists in the employee CSV file.

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
    Check if admin credentials are set in the admin file.

    Returns:
        tuple: (admin_username, admin_password) if credentials exist, else None
    """
    username = entry_username.get().strip()
    password = entry_password.get().strip()

    if not os.path.exists(config.ADMIN_DIR):
        return False
    with open(config.ADMIN_DIR, 'r') as f:
        lines = f.readlines()
        if len(lines) < 2:
            return False
        admin_username = lines[0].strip()
        admin_password = lines[1].strip()
        if username == admin_username and password == admin_password:
            return True
        return False

def change_password():
    """
    Change the admin password by verifying the current password and setting a new one.

    Validates inputs, checks current password, and updates the password in the file.
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

    # Gán lại command cho nút xác nhận
    change_pass_window.verify_button.config(command=do_change_password)



def SaveProfile():
    """
    Save employee profile (ID, name, image path, and embedding) after admin verification.

    Validates inputs, checks for duplicate IDs, and saves data to CSV after admin authentication.
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

    def verify_admin():
        """Verify admin credentials and save employee data if valid."""

        if check_admin_account():
            with open(config.EMPLOYEE_CSV, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([id_value, name_value, img_path, embedding_path])
            messagebox.showinfo("Success", f"Saved profile for ID: {id_value}, Name: {name_value}")

            txt.delete(0, 'end')
            txt2.delete(0, 'end')

            entry_username.delete(0, 'end')
            entry_password.delete(0, 'end')

            admin_window.withdraw()
            admin_window.grab_release()
        else:
            messagebox.showerror("Error", "Invalid username or password")

    admin_window.verify_button.config(command=verify_admin)
    admin_window.deiconify()
    admin_window.grab_set()

def TakeImages():
    """
    Capture an employee's face image using webcam and save it with embeddings.

    Validates inputs, checks for duplicate IDs, captures image on 's' key press,
    and saves both the image and its embedding.
    """
    os.makedirs(config.EMPLOYEE_DIR, exist_ok=True)

    # Initialize employee CSV if it doesn't exist
    if not os.path.exists(config.EMPLOYEE_CSV):
        with open(config.EMPLOYEE_CSV, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'name', 'img_path', 'embedding'])
        print(f"Created CSV file: {config.EMPLOYEE_CSV}")

    id_value = txt.get()
    name_value = txt2.get()

    if validate_input(id_value, name_value) and not check_id_exists(id_value,config.EMPLOYEE_CSV):
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

    # Initialize today's attendance CSV
    csv_filename = today.strftime("%Y-%m-%d") + ".csv"
    csv_filepath = os.path.join(report_dir, csv_filename)
    if not os.path.exists(csv_filepath):
        with open(csv_filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'name', 'date', time_col])
        print(f"Created CSV file: {csv_filepath}")

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
            # Điều kiện cho checkin/checkout
            if (current_time - start_time >= time_out/2):
                if type_ == "checkin":
                    can_write = distant <= threshold and not check_id_exists(id, csv_filepath)
                else:
                    # Chỉ cho checkout nếu đã checkin và chưa checkout
                    checkin_file = os.path.join(config.ATTENDANCE_REPORT, csv_filename)
                    can_write = (distant <= threshold and not check_id_exists(id, csv_filepath)
                                 and check_id_exists(id, checkin_file))
                if can_write :
                    date_str = today.strftime("%d-%m-%Y")
                    time_str = today.strftime("%H:%M:%S")
                    attendance = [str(id), identity, date_str, time_str]
                    with open(csv_filepath, 'a', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow(attendance)
                    messagebox.showinfo("Success", success_msg)
                    break
                elif check_id_exists(id, csv_filepath):
                    messagebox.showinfo("Info", f"ID {id} already {type_}ed today.")
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
            messagebox.showinfo("Error", "Fake Face Detected!")
            break

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    load_attendance_to_table(report_dir)
    cap.release()
    cv2.destroyAllWindows()

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
change_pass_btn.pack(pady=10)

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

trainImg = tkinter.Button(frame1, text="Save Profile", fg="black", command=SaveProfile, bg="#00aeff", width=34, height=1, activebackground="white", font=('times', 16, ' bold '))
trainImg.place(x=30, y=430, relwidth=0.89)

trackImg = tkinter.Button(frame2, text="Checkin", command=lambda: Attendance("checkin"), fg="black", bg="#00aeff", height=1, activebackground="white", font=('times', 16, ' bold '))
trackImg.place(x=30, y=60, relwidth=0.44)

checkoutBtn = tkinter.Button(frame2, text="Checkout", command=lambda: Attendance("checkout"), fg="black", bg="#00aeff", height=1, activebackground="white", font=('times', 16, ' bold '))
checkoutBtn.place(relx=0.52, x=0, y=60, relwidth=0.44)

quitWindow = tkinter.Button(frame2, text="Quit", command=window.destroy, fg="white", bg="#13059c", width=35, height=1, activebackground="white", font=('times', 16, ' bold '))
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