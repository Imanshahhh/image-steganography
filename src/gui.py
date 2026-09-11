"""Desktop interface for the Image Steganography assignment.

Run from the project root with: ``python src/gui.py``.
The interface uses the project's existing steganography and analysis functions.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QFileDialog, QFormLayout, QGroupBox, QHBoxLayout, QLabel,
    QFrame, QLineEdit, QMainWindow, QMessageBox, QPushButton, QTabWidget, QTextEdit,
    QVBoxLayout, QWidget,
)

from analysis import save_histogram_comparison, save_visual_comparison
from stego_core import (
    analyze_file_size, calculate_available_secret_capacity, calculate_mse,
    calculate_psnr, embed, extract, load_cover_image,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "assets" / "output"
IMAGE_FILTER = "Lossless Images (*.png *.bmp)"
SECRET_FILTER = "Supported files (*.txt *.pdf *.doc *.docx *.png *.jpg *.jpeg)"


def human_size(size: int) -> str:
    """Present file sizes in a report-friendly form."""
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.2f} {unit}"
        size /= 1024
    return f"{size} B"


class FilePicker(QWidget):
    def __init__(self, label: str, file_filter: str, save: bool = False):
        super().__init__()
        self.file_filter, self.save = file_filter, save
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Choose a file...")
        self.path_edit.setMinimumHeight(38)
        button = QPushButton("Browse")
        button.setObjectName("secondaryButton")
        button.setMinimumHeight(38)
        button.clicked.connect(self.choose_file)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QLabel(label))
        layout.addWidget(self.path_edit, 1)
        layout.addWidget(button)

    def choose_file(self) -> None:
        current = self.path_edit.text() or str(PROJECT_ROOT)
        if self.save:
            path, _ = QFileDialog.getSaveFileName(self, "Save stego image", current, "PNG image (*.png)")
            if path and not path.lower().endswith(".png"):
                path += ".png"
        else:
            path, _ = QFileDialog.getOpenFileName(self, "Choose file", current, self.file_filter)
        if path:
            self.path_edit.setText(path)

    def path(self) -> str:
        return self.path_edit.text().strip()


class SteganographyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Steganography Tool")
        self.resize(1020, 720)
        self.setMinimumSize(900, 640)
        self._build_interface()
        self._apply_theme()

    def _apply_theme(self) -> None:
        """Apply a consistent dark security-dashboard appearance."""
        self.setStyleSheet("""
            QMainWindow, QWidget#appSurface { background: #07111f; }
            QWidget { color: #d8e5f2; font-family: "Segoe UI", Arial, sans-serif; font-size: 13px; }
            QFrame#hero { background: #0c1c2f; border: 1px solid #1d3b58; border-radius: 16px; }
            QLabel#brandMark { background: #18b7a0; color: #04201d; border-radius: 22px; font-size: 22px; font-weight: 800; padding: 8px; }
            QLabel#appTitle { color: #f7fbff; font-size: 25px; font-weight: 700; }
            QLabel#appSubtitle { color: #9eb3c7; font-size: 13px; }
            QLabel#badge { background: #123a54; color: #75d9ff; border-radius: 10px; padding: 5px 10px; font-size: 11px; font-weight: 700; }
            QLabel#pageEyebrow { color: #38d3bd; font-size: 11px; font-weight: 700; letter-spacing: 0.7px; }
            QLabel#pageTitle { color: #f5f9ff; font-size: 19px; font-weight: 700; }
            QLabel#pageHint { color: #9eb3c7; font-size: 13px; }
            QTabWidget::pane { background: #0b1829; border: 1px solid #1d3650; border-radius: 12px; top: -1px; }
            QTabBar::tab { background: transparent; color: #86a0b8; border: 0; padding: 12px 22px; margin-right: 4px; font-weight: 600; }
            QTabBar::tab:selected { color: #f7fbff; background: #15304b; border-top-left-radius: 8px; border-top-right-radius: 8px; }
            QTabBar::tab:hover:!selected { color: #dceaf7; }
            QGroupBox { background: #0f2135; color: #eaf3fb; font-size: 13px; font-weight: 700; border: 1px solid #23435f; border-radius: 10px; margin-top: 14px; padding: 17px 14px 13px 14px; }
            QGroupBox::title { subcontrol-origin: margin; left: 13px; padding: 0 6px; }
            QLabel { color: #c8d8e7; }
            QLineEdit { background: #081421; color: #f4f8fc; border: 1px solid #2d4d68; border-radius: 7px; padding: 0 10px; selection-background-color: #1a6d94; }
            QLineEdit:focus { border: 1px solid #32c7b3; }
            QPushButton { background: #1bb89f; color: #03221d; border: 0; border-radius: 7px; padding: 10px 17px; font-weight: 700; }
            QPushButton:hover { background: #38d3bd; }
            QPushButton:pressed { background: #12927f; }
            QPushButton#secondaryButton { background: #193650; color: #cbe7fa; border: 1px solid #315878; padding: 7px 15px; }
            QPushButton#secondaryButton:hover { background: #244967; }
            QTextEdit { background: #081421; color: #b9ccdd; border: 1px solid #23435f; border-radius: 9px; padding: 13px; font-family: "Cascadia Mono", Consolas, monospace; font-size: 12px; }
            QTextEdit:focus { border: 1px solid #32c7b3; }
        """)

    def _build_interface(self) -> None:
        central = QWidget()
        central.setObjectName("appSurface")
        layout = QVBoxLayout(central)
        layout.setContentsMargins(28, 24, 28, 28)
        layout.setSpacing(18)
        layout.addWidget(self._build_header())
        tabs = QTabWidget()
        tabs.addTab(self._build_embed_tab(), "Hide file")
        tabs.addTab(self._build_extract_tab(), "Extract file")
        tabs.addTab(self._build_analysis_tab(), "Analyse results")
        layout.addWidget(tabs, 1)
        self.setCentralWidget(central)

    @staticmethod
    def _page_intro(eyebrow: str, title: str, hint: str) -> QWidget:
        intro = QWidget()
        layout = QVBoxLayout(intro)
        layout.setContentsMargins(10, 10, 10, 0)
        layout.setSpacing(3)
        tag, heading, description = QLabel(eyebrow), QLabel(title), QLabel(hint)
        tag.setObjectName("pageEyebrow")
        heading.setObjectName("pageTitle")
        description.setObjectName("pageHint")
        description.setWordWrap(True)
        layout.addWidget(tag)
        layout.addWidget(heading)
        layout.addWidget(description)
        return intro

    @staticmethod
    def _build_header() -> QFrame:
        hero = QFrame()
        hero.setObjectName("hero")
        layout = QHBoxLayout(hero)
        layout.setContentsMargins(20, 16, 20, 16)
        mark = QLabel("⌁")
        mark.setObjectName("brandMark")
        mark.setFixedSize(48, 48)
        mark.setAlignment(Qt.AlignCenter)
        copy = QVBoxLayout()
        copy.setSpacing(2)
        title, subtitle = QLabel("StegoVault"), QLabel("Secure image steganography workspace")
        title.setObjectName("appTitle")
        subtitle.setObjectName("appSubtitle")
        copy.addWidget(title)
        copy.addWidget(subtitle)
        badge = QLabel("LSB · PNG SAFE")
        badge.setObjectName("badge")
        layout.addWidget(mark)
        layout.addLayout(copy)
        layout.addStretch()
        layout.addWidget(badge, alignment=Qt.AlignTop)
        return hero

    def _build_embed_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(14, 12, 14, 14)
        layout.setSpacing(10)
        layout.addWidget(self._page_intro("WORKFLOW 01", "Protect a file inside an image", "Choose a PNG cover image and a supported secret file. The capacity checker keeps your payload safe."))
        files = QGroupBox("1. Choose files")
        form = QVBoxLayout(files)
        self.cover_picker = FilePicker("Cover image:", IMAGE_FILTER)
        self.secret_picker = FilePicker("Secret file:", SECRET_FILTER)
        self.output_picker = FilePicker("Stego image:", "", save=True)
        self.output_picker.path_edit.setText(str(OUTPUT_DIR / "stego.png"))
        self.cover_picker.path_edit.editingFinished.connect(self.update_capacity)
        self.secret_picker.path_edit.editingFinished.connect(self.update_capacity)
        for picker in (self.cover_picker, self.secret_picker, self.output_picker):
            form.addWidget(picker)
        layout.addWidget(files)
        capacity = QGroupBox("2. Capacity check")
        status = QFormLayout(capacity)
        self.capacity_label = QLabel("Choose a cover image and secret file.")
        self.capacity_label.setWordWrap(True)
        status.addRow("Available capacity:", self.capacity_label)
        layout.addWidget(capacity)
        button = QPushButton("Hide file and create stego image")
        button.setMinimumHeight(42)
        button.clicked.connect(self.hide_file)
        layout.addWidget(button, alignment=Qt.AlignLeft)
        self.embed_log = self.make_log()
        layout.addWidget(self.embed_log, 1)
        return page

    def _build_extract_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(14, 12, 14, 14)
        layout.setSpacing(10)
        layout.addWidget(self._page_intro("WORKFLOW 02", "Recover your hidden content", "Load a stego image created by this tool and save the recovered file to a folder you choose."))
        files = QGroupBox("Recover a secret file")
        form = QVBoxLayout(files)
        self.stego_picker = FilePicker("Stego image:", IMAGE_FILTER)
        self.extract_dir = QLineEdit(str(OUTPUT_DIR / "extracted"))
        form.addWidget(self.stego_picker)
        row = QHBoxLayout()
        row.addWidget(QLabel("Save extracted file to:"))
        row.addWidget(self.extract_dir, 1)
        browse = QPushButton("Browse")
        browse.clicked.connect(self.choose_extract_dir)
        row.addWidget(browse)
        form.addLayout(row)
        layout.addWidget(files)
        button = QPushButton("Extract hidden file")
        button.setMinimumHeight(42)
        button.clicked.connect(self.extract_file)
        layout.addWidget(button, alignment=Qt.AlignLeft)
        self.extract_log = self.make_log()
        layout.addWidget(self.extract_log, 1)
        return page

    def _build_analysis_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(14, 12, 14, 14)
        layout.setSpacing(10)
        layout.addWidget(self._page_intro("WORKFLOW 03", "Validate the stego image", "Generate visual, histogram, quality, and file-size evidence ready to include in your assignment report."))
        files = QGroupBox("Compare cover and stego images")
        form = QVBoxLayout(files)
        self.analysis_cover = FilePicker("Cover image:", IMAGE_FILTER)
        self.analysis_stego = FilePicker("Stego image:", IMAGE_FILTER)
        form.addWidget(self.analysis_cover)
        form.addWidget(self.analysis_stego)
        layout.addWidget(files)
        button = QPushButton("Calculate metrics and save report images")
        button.setMinimumHeight(42)
        button.clicked.connect(self.analyse_images)
        layout.addWidget(button, alignment=Qt.AlignLeft)
        self.analysis_log = self.make_log()
        layout.addWidget(self.analysis_log, 1)
        return page

    @staticmethod
    def make_log() -> QTextEdit:
        log = QTextEdit()
        log.setReadOnly(True)
        log.setPlaceholderText("Results will appear here.")
        return log

    def update_capacity(self) -> None:
        try:
            cover, secret = Path(self.cover_picker.path()), Path(self.secret_picker.path())
            if not cover.is_file():
                self.capacity_label.setText("Choose a cover image.")
                return
            available = calculate_available_secret_capacity(load_cover_image(cover))
            message = f"{human_size(available)} available for the secret file."
            if secret.is_file():
                message += " Fits." if secret.stat().st_size <= available else " Does not fit - choose a larger cover image."
            self.capacity_label.setText(message)
        except Exception as error:
            self.capacity_label.setText(f"Unable to calculate capacity: {error}")

    def hide_file(self) -> None:
        try:
            result = embed(self.cover_picker.path(), self.secret_picker.path(), self.output_picker.path())
            output = result["output_path"]
            self.stego_picker.path_edit.setText(output)
            self.analysis_cover.path_edit.setText(self.cover_picker.path())
            self.analysis_stego.path_edit.setText(output)
            self.embed_log.setPlainText(
                "Stego image created successfully.\n\n"
                f"Output: {output}\nSecret size: {human_size(result['secret_size'])}\n"
                f"Payload (including header): {human_size(result['payload_size'])}\n"
                f"Image capacity: {human_size(result['capacity'])}\n"
                f"Remaining capacity: {human_size(result['remaining_capacity'])}\n\n"
                "Next: use the Analyse results tab to create the histogram and visual-comparison screenshots."
            )
        except Exception as error:
            self.show_error("Unable to hide file", error)

    def choose_extract_dir(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Choose output folder", self.extract_dir.text())
        if directory:
            self.extract_dir.setText(directory)

    def extract_file(self) -> None:
        try:
            result = extract(self.stego_picker.path(), self.extract_dir.text())
            self.extract_log.setPlainText(
                "Secret file extracted successfully.\n\n"
                f"Output: {result['output_path']}\nFile type: {result['extension']}\n"
                f"File size: {human_size(result['file_size'])}"
            )
        except Exception as error:
            self.show_error("Unable to extract file", error)

    def analyse_images(self) -> None:
        try:
            cover, stego = self.analysis_cover.path(), self.analysis_stego.path()
            mse, psnr = calculate_mse(cover, stego), calculate_psnr(cover, stego)
            sizes = analyze_file_size(cover, stego)
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            histogram, visual = OUTPUT_DIR / "histogram_comparison.png", OUTPUT_DIR / "visual_comparison.png"
            save_histogram_comparison(cover, stego, histogram)
            save_visual_comparison(cover, stego, visual)
            psnr_text = "Infinite (identical)" if psnr == float("inf") else f"{psnr:.2f} dB"
            self.analysis_log.setPlainText(
                "Analysis complete. Add the two saved images to your report.\n\n"
                f"MSE: {mse:.6f}\nPSNR: {psnr_text}\n\n"
                f"Cover file size: {human_size(sizes['cover_size'])}\nStego file size: {human_size(sizes['stego_size'])}\n"
                f"Difference: {sizes['difference']:+,} bytes ({sizes['percentage_change']:+.2f}%)\n\n"
                f"Histogram: {histogram}\nVisual comparison: {visual}\n\n"
                "PNG is used because lossy formats such as JPEG can destroy hidden LSB data."
            )
        except Exception as error:
            self.show_error("Unable to analyse images", error)

    def show_error(self, title: str, error: Exception) -> None:
        QMessageBox.critical(self, title, str(error))


def main() -> int:
    app = QApplication(sys.argv)
    window = SteganographyWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
