from tkinter import *
from tkinter import ttk, simpledialog, messagebox
import threading
import time

# --- Data Models ---
class Question:
    def __init__(self, text, options, correct_index, points, category):
        self.text = text
        self.options = options
        self.correct_index = correct_index
        self.points = points
        self.category = category

    def check_answer(self, index):
        return index == self.correct_index

class Quiz:
    def __init__(self, title, description, time_limit_minutes):
        self.title = title
        self.description = description
        self.time_limit = time_limit_minutes * 60
        self.questions = []

    def add_question(self, question):
        self.questions.append(question)

class User:
    def __init__(self, username, role):
        self.username = username
        self.role = role

class QuizSystem:
    def __init__(self):
        self.users = {}
        self.quizzes = []

    def register_user(self, username, role):
        self.users[username] = User(username, role)

    def login(self, username):
        return self.users.get(username)

# --- GUI Application ---
class QuizApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Quiz App")
        self.root.geometry("700x500")
        self.root.configure(bg='white')

        self.system = QuizSystem()
        self.current_user = None
        self.current_quiz = None
        self.question_index = 0
        self.score = 0
        self.category_scores = {}
        self.remaining_time = 0
        self.timer_thread = None

        self.style = ttk.Style()
        self.style.configure("TButton", padding=6, relief="flat", background="#e1e1e1")
        self.style.configure("TLabel", background="white", font=("Arial", 12))
        self.style.configure("TEntry", padding=5)

        self.build_login_screen()

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def build_login_screen(self):
        self.clear_window()
        frame = Frame(self.root, bg='white')
        frame.pack(pady=50)

        ttk.Label(frame, text="Username:").grid(row=0, column=0, pady=5, sticky=W)
        self.username_entry = ttk.Entry(frame)
        self.username_entry.grid(row=0, column=1, pady=5)

        ttk.Label(frame, text="Role:").grid(row=1, column=0, pady=5, sticky=W)
        self.role_var = StringVar(value="student")
        ttk.Radiobutton(frame, text="Student", variable=self.role_var, value="student").grid(row=1, column=1, sticky=W)
        ttk.Radiobutton(frame, text="Teacher", variable=self.role_var, value="teacher").grid(row=2, column=1, sticky=W)

        ttk.Button(frame, text="Register", command=self.register).grid(row=3, column=0, pady=10)
        ttk.Button(frame, text="Login", command=self.login).grid(row=3, column=1, pady=10)

    def register(self):
        username = self.username_entry.get()
        role = self.role_var.get()
        self.system.register_user(username, role)
        messagebox.showinfo("Success", "User registered successfully.")

    def login(self):
        username = self.username_entry.get()
        user = self.system.login(username)
        if not user:
            messagebox.showerror("Error", "User not found.")
            return
        self.current_user = user
        if user.role == "teacher":
            self.teacher_menu()
        else:
            self.student_menu()

    def teacher_menu(self):
        self.clear_window()
        ttk.Label(self.root, text=f"Welcome, {self.current_user.username} (Teacher)", font=("Arial", 16)).pack(pady=20)
        ttk.Button(self.root, text="Create Quiz", command=self.create_quiz_screen).pack(pady=10)
        ttk.Button(self.root, text="Logout", command=self.build_login_screen).pack(pady=10)

    def create_quiz_screen(self):
        self.clear_window()
        ttk.Label(self.root, text="Create Quiz", font=("Arial", 16)).pack(pady=10)

        frame = Frame(self.root, bg='white')
        frame.pack(pady=20)

        title_label = ttk.Label(frame, text="Quiz Title:")
        title_label.grid(row=0, column=0, sticky=W)
        title_entry = ttk.Entry(frame)
        title_entry.grid(row=0, column=1, pady=5)

        desc_label = ttk.Label(frame, text="Description:")
        desc_label.grid(row=1, column=0, sticky=W)
        desc_entry = ttk.Entry(frame)
        desc_entry.grid(row=1, column=1, pady=5)

        time_label = ttk.Label(frame, text="Time Limit (min):")
        time_label.grid(row=2, column=0, sticky=W)
        time_entry = ttk.Entry(frame)
        time_entry.grid(row=2, column=1, pady=5)

        def add_questions():
            try:
                title = title_entry.get()
                desc = desc_entry.get()
                time_limit = int(time_entry.get())
                quiz = Quiz(title, desc, time_limit)

                while True:
                    q_text = simpledialog.askstring("Question", "Enter question text:")
                    options = [simpledialog.askstring("Option", f"Option {i+1}:") for i in range(4)]
                    correct = simpledialog.askinteger("Correct", "Enter correct option number (1-4):") - 1
                    points = simpledialog.askinteger("Points", "Point value for this question:")
                    category = simpledialog.askstring("Category", "Enter category/topic:")
                    quiz.add_question(Question(q_text, options, correct, points, category))
                    more = messagebox.askyesno("Continue", "Add another question?")
                    if not more:
                        break

                self.system.quizzes.append(quiz)
                messagebox.showinfo("Done", "Quiz created successfully!")
                self.teacher_menu()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create quiz: {e}")

        ttk.Button(self.root, text="Add Questions", command=add_questions).pack(pady=10)
        ttk.Button(self.root, text="Back", command=self.teacher_menu).pack()

    def student_menu(self):
        self.clear_window()
        ttk.Label(self.root, text=f"Welcome, {self.current_user.username} (Student)", font=("Arial", 16)).pack(pady=20)

        for quiz in self.system.quizzes:
            ttk.Button(self.root, text=quiz.title, command=lambda q=quiz: self.start_quiz(q)).pack(pady=5)

        ttk.Button(self.root, text="Logout", command=self.build_login_screen).pack(pady=10)

    def start_quiz(self, quiz):
        self.current_quiz = quiz
        self.question_index = 0
        self.score = 0
        self.category_scores = {}
        self.remaining_time = quiz.time_limit
        self.timer_thread = threading.Thread(target=self.countdown_timer)
        self.timer_thread.daemon = True
        self.timer_thread.start()
        self.show_question()

    def countdown_timer(self):
        while self.remaining_time > 0:
            time.sleep(1)
            self.remaining_time -= 1
        messagebox.showinfo("Time's Up", "Time is over!")
        self.show_results()

    def show_question(self):
        if self.remaining_time <= 0 or self.question_index >= len(self.current_quiz.questions):
            self.show_results()
            return

        question = self.current_quiz.questions[self.question_index]
        self.clear_window()

        ttk.Label(self.root, text=f"Time left: {int(self.remaining_time)}s", font=("Arial", 12)).pack(pady=5)
        ttk.Label(self.root, text=f"Q{self.question_index + 1}: {question.text}", font=("Arial", 14)).pack(pady=10)

        self.selected = IntVar()
        for i, option in enumerate(question.options):
            ttk.Radiobutton(self.root, text=option, variable=self.selected, value=i).pack(anchor='w', padx=20)

        ttk.Button(self.root, text="Next", command=self.submit_answer).pack(pady=10)

    def submit_answer(self):
        selected_index = self.selected.get()
        question = self.current_quiz.questions[self.question_index]
        if question.check_answer(selected_index):
            self.score += question.points
            cat = question.category
            self.category_scores[cat] = self.category_scores.get(cat, 0) + question.points

        self.question_index += 1
        self.show_question()

    def show_results(self):
        self.clear_window()
        ttk.Label(self.root, text="Quiz Completed!", font=("Arial", 16)).pack(pady=10)
        ttk.Label(self.root, text=f"Total Score: {self.score}", font=("Arial", 14)).pack(pady=10)

        ttk.Label(self.root, text="Category Breakdown:", font=("Arial", 12)).pack(pady=5)
        for cat, pts in self.category_scores.items():
            ttk.Label(self.root, text=f"{cat}: {pts}").pack()

        ttk.Button(self.root, text="Back to Menu", command=self.student_menu).pack(pady=10)

# --- Run the GUI ---
root = Tk()
app = QuizApp(root)
root.mainloop()
