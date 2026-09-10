import tkinter as tk


class HomeworkGradingWindow(tk.Tk):
    """Window for displaying texts and collecting grade/feedback answers."""

    def __init__(self, text_sets=None, require_grade=True, assignment_label=None):
        super().__init__()
        self.title("Homework Grading")
        self.geometry("1100x600")
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=2)
        self.rowconfigure(1, weight=1)

        self.text_sets = list(text_sets or [])
        self.submissions = []
        self.require_grade = require_grade
        self.current_text = False
        self.current_assignment_text = None

        assignment_frame = tk.LabelFrame(
            self,
            text=assignment_label
            or (
                "Assignment text" if require_grade else "Previous grading and feedback"
            ),
        )
        assignment_frame.grid(
            row=0, column=0, columnspan=2, sticky="ew", padx=12, pady=12
        )
        assignment_frame.columnconfigure(0, weight=1)
        assignment_frame.rowconfigure(0, weight=1)

        self.assignment_text = tk.Text(
            assignment_frame, height=8, wrap="word", state="disabled"
        )
        self.assignment_text.grid(row=0, column=0, sticky="ew", padx=(8, 0), pady=8)

        assignment_scrollbar = tk.Scrollbar(
            assignment_frame, orient="vertical", command=self.assignment_text.yview
        )
        assignment_scrollbar.grid(row=0, column=1, sticky="ns", padx=(0, 8), pady=8)
        self.assignment_text.config(yscrollcommand=assignment_scrollbar.set)

        input_frame = tk.Frame(self)
        input_frame.grid(row=1, column=0, sticky="nsew", padx=(12, 6), pady=(0, 12))
        input_frame.columnconfigure(0, weight=1)
        input_frame.rowconfigure(3, weight=1)

        grade_frame = tk.Frame(input_frame)
        grade_frame.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        grade_frame.columnconfigure(0, weight=1)
        grade_frame.columnconfigure(1, weight=1)

        grade_label = tk.Label(grade_frame, text="Grade")
        grade_label.grid(row=0, column=0, columnspan=2, sticky="w")

        self.grade_entry = tk.Entry(grade_frame)
        self.grade_entry.grid(row=1, column=0, sticky="ew", padx=(0, 4))

        self.maximum_grade_entry = tk.Entry(grade_frame)
        self.maximum_grade_entry.grid(row=1, column=1, sticky="ew", padx=(4, 0))

        feedback_label = tk.Label(input_frame, text="Feedback")
        feedback_label.grid(row=2, column=0, sticky="w", pady=(12, 4))

        self.feedback_text = tk.Text(input_frame, height=10, wrap="word")
        self.feedback_text.grid(row=3, column=0, sticky="nsew")

        self.submit_button = tk.Button(input_frame, text="Submit", command=self.submit)
        self.submit_button.grid(row=4, column=0, sticky="w", pady=(12, 0))
        self.bind("<Control-s>", self.submit)

        if not self.require_grade:
            grade_frame.grid_remove()
            feedback_label.grid(row=0, column=0, sticky="w", pady=(0, 4))
            self.feedback_text.grid(row=1, column=0, sticky="nsew")
            self.submit_button.grid(row=2, column=0, sticky="w", pady=(12, 0))
            input_frame.rowconfigure(1, weight=1)

        student_frame = tk.LabelFrame(self, text="Student answer")
        student_frame.grid(row=1, column=1, sticky="nsew", padx=(6, 12), pady=(0, 12))
        student_frame.columnconfigure(0, weight=1)
        student_frame.rowconfigure(0, weight=1)

        self.student_answer = tk.Text(student_frame, wrap="word", state="disabled")
        self.student_answer.grid(row=0, column=0, sticky="nsew", padx=(8, 0), pady=8)

        student_scrollbar = tk.Scrollbar(
            student_frame, orient="vertical", command=self.student_answer.yview
        )
        student_scrollbar.grid(row=0, column=1, sticky="ns", padx=(0, 8), pady=8)
        self.student_answer.config(yscrollcommand=student_scrollbar.set)

        self.add_texts_from_queue()

    def add_text(self, student_answer, assignment_text):
        """Display another student answer and assignment text."""
        self.text_sets.append((student_answer, assignment_text))
        if not self.current_text:
            self.add_texts_from_queue()

    def add_texts_from_queue(self):
        if not self.text_sets:
            return
        next_student_answer, next_assignment_text = self.text_sets.pop(0)
        self.current_text = True
        self.grade_entry.delete(0, tk.END)
        if next_assignment_text != self.current_assignment_text:
            self.maximum_grade_entry.delete(0, tk.END)
        self.feedback_text.delete("1.0", tk.END)
        self._set_read_only_text(self.assignment_text, next_assignment_text)
        self._set_read_only_text(self.student_answer, next_student_answer)
        self.assignment_text.yview_moveto(0)
        self.student_answer.yview_moveto(0)
        self.current_assignment_text = next_assignment_text
        if self.require_grade:
            self.grade_entry.focus_set()
            self.grade_entry.icursor(0)
        else:
            self.feedback_text.focus_set()

    @staticmethod
    def _set_read_only_text(widget, value):
        widget.config(state="normal")
        widget.delete("1.0", tk.END)
        widget.insert("1.0", value)
        widget.config(state="disabled")

    def submit(self, event=None):
        if self.require_grade:
            try:
                grade = int(self.grade_entry.get().strip())
                maximum_grade = int(self.maximum_grade_entry.get().strip())
            except ValueError:
                return "break"
            grade_text = f"{grade}/{maximum_grade}"
        else:
            grade_text = ""

        self.submissions.append(
            {
                "grade": grade_text,
                "feedback": self.feedback_text.get("1.0", "end-1c"),
            }
        )
        if self.text_sets:
            self.add_texts_from_queue()
        else:
            self.current_text = False
            self.submit_button.config(state="disabled")
            self.destroy()
        return "break"

    def get_answers(self):
        """Return a copy of all submitted grade and feedback values."""
        return list(self.submissions)

    def show(self):
        """Show the window and process its events until it is closed."""
        self.mainloop()


def create_window(text_sets=None, require_grade=True, assignment_label=None):
    """Create a HomeworkGradingWindow for compatibility with existing code."""
    return HomeworkGradingWindow(text_sets, require_grade, assignment_label)


if __name__ == "__main__":
    window = HomeworkGradingWindow(
        text_sets=[
            ("Student answer 1", "Assignment text 1"),
            ("Student answer 2", "Assignment text 2"),
            ("Student answer 3", "Assignment text 3"),
        ]
    )
    window.show()
