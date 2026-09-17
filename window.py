import tkinter as tk


class PdfViewer(tk.Canvas):
    """Display all pages of a PDF in a scrollable canvas."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self._images = []
        self._pdf_path = None
        self._clips = None
        self._zoom = 1.0
        self.bind("<Configure>", self._handle_resize)
        self.bind("<MouseWheel>", self._scroll_with_mouse)
        self.bind("<Button-4>", self._scroll_with_mouse)
        self.bind("<Button-5>", self._scroll_with_mouse)

    def show_pdf(self, pdf_path, clips=None):
        self._pdf_path = pdf_path
        self._clips = clips
        self._zoom = 1.0
        self._render()

    def zoom_in(self):
        self._zoom = min(self._zoom * 1.25, 4.0)
        self._render()

    def zoom_out(self):
        self._zoom = max(self._zoom / 1.25, 0.5)
        self._render()

    def reset_zoom(self):
        self._zoom = 1.0
        self._render()

    def _render(self):
        self.delete("all")
        self._images = []
        pdf_path = self._pdf_path
        if pdf_path is None:
            self.configure(scrollregion=(0, 0, 0, 0))
            return

        import pymupdf

        with pymupdf.open(pdf_path) as pdf:
            y_position = 8
            available_width = max(self.winfo_width() - 16, 500)
            pages = (
                ((pdf[page_number], clip) for page_number, clip in self._clips)
                if self._clips is not None
                else ((page, None) for page in pdf)
            )
            for page, clip in pages:
                page_width = clip.width if clip is not None else page.rect.width
                scale = available_width / page_width * self._zoom
                pixmap = page.get_pixmap(
                    matrix=pymupdf.Matrix(scale, scale), clip=clip, alpha=False
                )
                image = tk.PhotoImage(data=pixmap.tobytes("ppm"))
                self._images.append(image)
                self.create_image(8, y_position, image=image, anchor="nw")
                y_position += image.height() + 12
        self.configure(
            scrollregion=(0, 0, available_width * self._zoom + 16, y_position)
        )

    def _handle_resize(self, event):
        if event.width > 1 and self._pdf_path is not None and self._zoom == 1.0:
            self._render()

    def _scroll_with_mouse(self, event):
        event_number = getattr(event, "num", None)
        if event_number == 4:
            self.yview_scroll(-3, "units")
        elif event_number == 5:
            self.yview_scroll(3, "units")
        else:
            self.yview_scroll(-event.delta // 120, "units")
        return "break"


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
        assignment_frame.rowconfigure(1, weight=1)

        assignment_zoom_frame = tk.Frame(assignment_frame)
        assignment_zoom_frame.grid(
            row=0, column=0, columnspan=2, sticky="ew", padx=8, pady=(4, 0)
        )
        assignment_zoom_frame.columnconfigure(1, weight=1)
        tk.Button(
            assignment_zoom_frame, text="-", width=3, command=self._assignment_zoom_out
        ).grid(row=0, column=0, sticky="w")
        self.assignment_zoom_label = tk.Label(assignment_zoom_frame, text="100%")
        self.assignment_zoom_label.grid(row=0, column=1)
        tk.Button(
            assignment_zoom_frame, text="+", width=3, command=self._assignment_zoom_in
        ).grid(row=0, column=2, sticky="e")

        self.assignment_text = tk.Text(
            assignment_frame, height=8, wrap="word", state="disabled"
        )
        self.assignment_text.grid(row=1, column=0, sticky="nsew", padx=(8, 0), pady=8)

        assignment_scrollbar = tk.Scrollbar(
            assignment_frame, orient="vertical", command=self.assignment_text.yview
        )
        assignment_scrollbar.grid(row=1, column=1, sticky="ns", padx=(0, 8), pady=8)
        self.assignment_text.config(yscrollcommand=assignment_scrollbar.set)
        self.assignment_scrollbar = assignment_scrollbar

        self.assignment_pdf = PdfViewer(
            assignment_frame, background="white", highlightthickness=0
        )
        self.assignment_pdf.grid(
            row=1, column=0, sticky="nsew", padx=(8, 0), pady=8
        )
        self.assignment_pdf.grid_remove()
        assignment_pdf_scrollbar = tk.Scrollbar(
            assignment_frame, orient="vertical", command=self.assignment_pdf.yview
        )
        assignment_pdf_scrollbar.grid(row=1, column=1, sticky="ns", padx=(0, 8), pady=8)
        assignment_pdf_scrollbar.grid_remove()
        assignment_pdf_horizontal_scrollbar = tk.Scrollbar(
            assignment_frame, orient="horizontal", command=self.assignment_pdf.xview
        )
        assignment_pdf_horizontal_scrollbar.grid(row=2, column=0, sticky="ew", padx=(8, 0))
        assignment_pdf_horizontal_scrollbar.grid_remove()
        self.assignment_pdf.config(
            yscrollcommand=assignment_pdf_scrollbar.set,
            xscrollcommand=assignment_pdf_horizontal_scrollbar.set,
        )
        self.assignment_pdf_scrollbar = assignment_pdf_scrollbar
        self.assignment_pdf_horizontal_scrollbar = assignment_pdf_horizontal_scrollbar

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
        student_frame.rowconfigure(1, weight=1)

        zoom_frame = tk.Frame(student_frame)
        zoom_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=8, pady=(4, 0))
        zoom_frame.columnconfigure(1, weight=1)
        tk.Button(zoom_frame, text="-", width=3, command=self._zoom_out).grid(
            row=0, column=0, sticky="w"
        )
        self.zoom_label = tk.Label(zoom_frame, text="100%")
        self.zoom_label.grid(row=0, column=1)
        tk.Button(zoom_frame, text="+", width=3, command=self._zoom_in).grid(
            row=0, column=2, sticky="e"
        )

        self.student_answer = PdfViewer(
            student_frame, background="white", highlightthickness=0
        )
        self.student_answer.grid(row=1, column=0, sticky="nsew", padx=(8, 0), pady=8)

        student_scrollbar = tk.Scrollbar(
            student_frame, orient="vertical", command=self.student_answer.yview
        )
        student_scrollbar.grid(row=1, column=1, sticky="ns", padx=(0, 8), pady=8)
        self.student_answer.config(yscrollcommand=student_scrollbar.set)

        horizontal_scrollbar = tk.Scrollbar(
            student_frame, orient="horizontal", command=self.student_answer.xview
        )
        horizontal_scrollbar.grid(row=2, column=0, sticky="ew", padx=(8, 0))
        self.student_answer.config(xscrollcommand=horizontal_scrollbar.set)

        self.add_texts_from_queue()

    def add_text(self, student_answer, assignment_text):
        """Display another student answer and assignment text."""
        self.text_sets.append((student_answer, assignment_text))
        if not self.current_text:
            self.add_texts_from_queue()

    def _zoom_in(self):
        self.student_answer.zoom_in()
        self.zoom_label.config(text=f"{self.student_answer._zoom:.0%}")

    def _zoom_out(self):
        self.student_answer.zoom_out()
        self.zoom_label.config(text=f"{self.student_answer._zoom:.0%}")

    def _assignment_zoom_in(self):
        self.assignment_pdf.zoom_in()
        self.assignment_zoom_label.config(text=f"{self.assignment_pdf._zoom:.0%}")

    def _assignment_zoom_out(self):
        self.assignment_pdf.zoom_out()
        self.assignment_zoom_label.config(text=f"{self.assignment_pdf._zoom:.0%}")

    def _show_assignment(self, assignment):
        if isinstance(assignment, tuple):
            assignment_pdf, clips = assignment
            self.assignment_text.grid_remove()
            self.assignment_scrollbar.grid_remove()
            self.assignment_pdf.grid()
            self.assignment_pdf_scrollbar.grid()
            self.assignment_pdf_horizontal_scrollbar.grid()
            self.assignment_pdf.show_pdf(assignment_pdf, clips)
            self.assignment_zoom_label.config(text="100%")
        else:
            self.assignment_pdf.grid_remove()
            self.assignment_pdf_scrollbar.grid_remove()
            self.assignment_pdf_horizontal_scrollbar.grid_remove()
            self.assignment_text.grid()
            self.assignment_scrollbar.grid()
            self._set_read_only_text(self.assignment_text, assignment)

    def add_texts_from_queue(self):
        if not self.text_sets:
            return
        next_student_answer, next_assignment_text = self.text_sets.pop(0)
        self.current_text = True
        self.grade_entry.delete(0, tk.END)
        if next_assignment_text != self.current_assignment_text:
            self.maximum_grade_entry.delete(0, tk.END)
        self.feedback_text.delete("1.0", tk.END)
        self._show_assignment(next_assignment_text)
        self.student_answer.show_pdf(next_student_answer)
        self.zoom_label.config(text="100%")
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
