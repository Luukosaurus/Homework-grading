"""Extract text from a PDF file."""

import argparse
import re
from pathlib import Path

import window


def pdf_to_text(pdf_path: Path) -> str:
    try:
        import pymupdf
    except ImportError as exc:
        raise SystemExit(
            "Install PyMuPDF with: pip install PyMuPDF (It Should be in the UV shit)"
        ) from exc

    text = []
    with pymupdf.open(pdf_path) as pdf:
        for page in pdf:
            text.append(page.get_text())
            text.append("\n")
    return "".join(text)


def split_answer_text(answer_text: str) -> list[str]:
    """Return the answer for each exercise in a correct-answer document."""
    answer_markers = list(re.finditer(r"Answer Exercise\s+(\d+)", answer_text))
    answers = []
    for marker in answer_markers:
        answer_start = marker.end()
        next_section = re.search(
            r"(?m)^Exercise\s+\d+\b|^Project preparation\b",
            answer_text[answer_start:],
        )
        answer_end = (
            answer_start + next_section.start() if next_section else len(answer_text)
        )
        answers.append(answer_text[answer_start:answer_end].strip())
    return answers


def make_text_from_files(
    answer_file: Path, assignment_directory: Path
) -> dict[tuple[str, int], tuple[str, str]]:
    """Build one answer/submission pair for every question and PDF."""
    answers = split_answer_text(pdf_to_text(answer_file))
    submissions = [
        (pdf.parent.name, pdf_to_text(pdf))
        for pdf in sorted((assignment_directory / "submissions").glob("s[0-9]*/*.pdf"))
    ]
    text_pairs = {}
    for question_number, answer in enumerate(answers, start=1):
        for submission_name, submission_text in submissions:
            text_pairs[(submission_name, question_number)] = (answer, submission_text)
    return text_pairs


def merge_answers(
    text_pairs: dict[tuple[str, int], tuple[str, str]],
    answers: list[dict[str, str]],
) -> list[dict[str, object]]:
    """Group question grades and feedback together for each submission."""
    grouped = {}
    for (submission_name, _), answer in zip(text_pairs, answers):
        grouped.setdefault(submission_name, []).append(answer)
    return [
        {"submission": submission_name, "answers": submission_answers}
        for submission_name, submission_answers in grouped.items()
    ]


def calculate_total_grade(answers: list[dict[str, str]]) -> str:
    """Calculate the total grade on a scale from zero to ten."""
    total_earned = 0
    total_possible = 0
    for answer in answers:
        earned, possible = (int(value) for value in answer["grade"].split("/", 1))
        total_earned += earned
        total_possible += possible

    if total_possible == 0:
        raise ValueError("Cannot calculate a grade with zero possible points")

    total_grade = total_earned / total_possible * 10
    return f"{total_grade:.2f}".rstrip("0").rstrip(".")


def write_feedback_files(
    submitted_answers: list[dict[str, object]],
    assignment_directory: Path,
    general_comments: dict[str, str] | None = None,
    final_comment: str = "",
) -> None:
    """Write the total grade and per-question feedback for each submission."""
    grade_header = re.compile(r"(?m)^=+\[Enter grade below\]=+[ \t]*$")
    feedback_header = re.compile(r"(?m)^=+\[Enter feedback below\]=+[ \t]*$")
    for submission in submitted_answers:
        feedback_path = (
            assignment_directory
            / "submissions"
            / submission["submission"]
            / "feedback.txt"
        )
        feedback_text = feedback_path.read_text()
        grade_section = grade_header.search(feedback_text)
        feedback_section = feedback_header.search(
            feedback_text, grade_section.end() if grade_section else 0
        )
        if grade_section is None or feedback_section is None:
            raise ValueError(f"Grade or feedback header not found in {feedback_path}")

        feedback_entries = []
        for answer in submission["answers"]:
            grade = answer["grade"].strip()
            feedback = answer["feedback"].strip()
            feedback_entries.append(f"{grade} {feedback}".rstrip())

        updated_text = (
            feedback_text[: grade_section.end()]
            + "\n"
            + calculate_total_grade(submission["answers"])
            + "\n"
            + feedback_text[feedback_section.start() : feedback_section.end()]
            + "\n\n"
            + "\n\n".join(feedback_entries)
            + "\n"
        )
        general_comment = (
            (general_comments or {}).get(submission["submission"], "").strip()
        )
        if general_comment:
            updated_text += "\n" + general_comment + "\n"
        if final_comment.strip():
            updated_text += "\n" + final_comment.strip() + "\n"
        feedback_path.write_text(updated_text)


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract text from a PDF file.")
    parser.add_argument("answer_file", type=Path, help="PDF containing the answers")
    parser.add_argument(
        "assignment_directory",
        type=Path,
        help="Directory containing submitted PDFs",
    )
    args = parser.parse_args()
    text_pairs = make_text_from_files(args.answer_file, args.assignment_directory)
    screen = window.create_window()
    for answer_text, submission_text in text_pairs.values():
        screen.add_text(submission_text, answer_text)
    screen.show()
    answers = (
        screen.get_answers()
    )  # This will return the submitted grade and feedback values
    submitted_answers = merge_answers(text_pairs, answers)
    submission_texts = {}
    for (submission_name, _), (_, submission_text) in text_pairs.items():
        submission_texts.setdefault(submission_name, submission_text)

    previous_feedback = {
        submission["submission"]: "\n\n".join(
            f'{answer["grade"].strip()} {answer["feedback"].strip()}'.rstrip()
            for answer in submission["answers"]
        )
        for submission in submitted_answers
    }
    general_screen = window.create_window(
        [
            (submission_texts[submission_name], previous_feedback[submission_name])
            for submission_name in submission_texts
        ],
        require_grade=False,
    )
    general_screen.show()
    general_answers = general_screen.get_answers()
    general_comments = {
        submission_name: answer["feedback"]
        for submission_name, answer in zip(submission_texts, general_answers)
    }
    final_screen = window.create_window(
        [("", "This comment will be added to every submission.")],
        require_grade=False,
        assignment_label="Final comment",
    )
    final_screen.show()
    final_answers = final_screen.get_answers()
    final_comment = final_answers[0]["feedback"] if final_answers else ""

    write_feedback_files(
        submitted_answers,
        args.assignment_directory,
        general_comments,
        final_comment,
    )
    print("Submitted answers:", submitted_answers)


if __name__ == "__main__":
    main()
