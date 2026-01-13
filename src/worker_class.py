"""
Worker class for background image processing.
"""

from pathlib import Path
from typing import List

from PySide6.QtCore import QObject, Signal

from src import constants
from src import imaging
from src import params_class


class BatchWorker(QObject):
    """Worker object executing image processing off the UI thread."""
    log_msg = Signal(str)
    progress = Signal(int, int)  # processed, total
    finished = Signal(int, int)  # processed, errors

    def __init__(self, folder: Path, params: params_class.ProcessingParams):
        super().__init__()
        self.folder = folder
        self.params_template = params
        self._stop = False

    def stop(self):
        """Request the worker to stop processing."""
        self._stop = True

    def get_output_folder(self) -> Path:
        """Get or create the output folder.

        Returns:
            Path: Path to the output folder
        """
        out_dir = self.folder / "_output"
        out_dir.mkdir(parents=True, exist_ok=True)
        return out_dir

    def run(self):
        """Main batch loop."""
        out_dir = self.get_output_folder()
        files: List[Path] = sorted([p for p in self.folder.iterdir()
                                   if p.is_file() and p.suffix.lower() in constants.SUPPORTED_EXTS])

        # Log settings with enabled/disabled flags
        exp_s = f"{self.params_template.exposure_factor:.2f}" if self.params_template.use_exposure else "disabled"
        sat_s = f"{self.params_template.saturation_val} (×{self.params_template.saturation_val/100:.2f})" if self.params_template.use_saturation else "disabled"
        ctr_s = f"{self.params_template.contrast_val} (×{self.params_template.contrast_val/100:.2f})" if self.params_template.use_contrast else "disabled"

        self.log_msg.emit(f"Source folder: {self.folder}")
        self.log_msg.emit(f"Output folder: {out_dir}")
        self.log_msg.emit(
            f"avoid_face_cropping={self.params_template.avoid_face_cropping}, "
            f"exposure={exp_s}, saturation={sat_s}, contrast={ctr_s}, jpg_quality={self.params_template.jpg_quality}"
        )

        if not files:
            self.log_msg.emit("No images found (supported: jpg, jpeg, png).")
            self.finished.emit(0, 0)
            return

        processed = 0
        errors = 0
        total = len(files)
        for p in files:
            if self._stop:
                break
            try:
                out_path = out_dir / p.stem
                # Clone template params with per-file paths
                file_params = self.params_template.with_paths(in_path=p, out_path=out_path)
                imaging.process_image(file_params)
                processed += 1
                self.log_msg.emit(f"OK  : {p.name} -> {out_path.name}.jpg")
            except Exception as e:
                errors += 1
                self.log_msg.emit(f"ERR : {p.name} -> {e}")
            self.progress.emit(processed, total)

        self.finished.emit(processed, errors)
