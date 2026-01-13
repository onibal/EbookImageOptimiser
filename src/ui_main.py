
# -*- coding: utf-8 -*-
"""
PySide6-based batch image processor for Kobo Libra Colour.
"""

import os
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import Qt, QThread
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QAbstractSpinBox, QSpinBox,
    QMainWindow, QWidget, QFileDialog,
    QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel,
    QGroupBox, QCheckBox, QSlider, QTextEdit
)

import constants
import params_class
import helper
import worker_class


# -----------------------------
# Main Window (UI)
# -----------------------------


class MainWindow(QMainWindow):
    """PySide6 application for batch processing images with Kobo-oriented settings."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("E-book Image Optimiser - Batch Image Processor")
        self.resize(840, 640)

        # Set window icon
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # State variables (kept as widget values)
        self.thread: Optional[QThread] = None
        self.worker: Optional[worker_class.BatchWorker] = None

        # Build UI
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(10)

        # Folder selection
        folder_box = QGroupBox("Folder")
        root.addWidget(folder_box)
        hb = QHBoxLayout(folder_box)
        self.folder_edit = QLineEdit(str(helper.get_script_dir()))
        self.folder_browse = QPushButton("Browse…")
        self.folder_browse.clicked.connect(self.on_browse)
        hb.addWidget(QLabel("Path:"))
        hb.addWidget(self.folder_edit, 1)
        hb.addWidget(self.folder_browse)

        # Options
        opts_box = QGroupBox("Options")
        root.addWidget(opts_box)
        vb_opts = QVBoxLayout(opts_box)

        # Crop options
        self.chk_crop = QCheckBox("Enable crop")
        self.chk_crop.setChecked(True)
        vb_opts.addWidget(self.chk_crop)

        # Crop dimensions
        crop_dim_layout = QHBoxLayout()
        crop_dim_layout.addWidget(QLabel("Width:"))
        self.crop_width = QSpinBox()
        self.crop_width.setRange(100, 10000)
        self.crop_width.setValue(1680)
        self.crop_width.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.crop_width.setEnabled(True)
        crop_dim_layout.addWidget(self.crop_width)

        crop_dim_layout.addWidget(QLabel("Height:"))
        self.crop_height = QSpinBox()
        self.crop_height.setRange(100, 10000)
        self.crop_height.setValue(1264)
        self.crop_height.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.crop_height.setEnabled(True)
        crop_dim_layout.addWidget(self.crop_height)

        # Add stretch to push dimensions to the left
        crop_dim_layout.addStretch(1)
        vb_opts.addLayout(crop_dim_layout)

        # Connect crop toggle to enable/disable dimension inputs
        def update_crop_widgets():
            enabled = self.chk_crop.isChecked()
            self.crop_width.setEnabled(enabled)
            self.crop_height.setEnabled(enabled)
            self.chk_avoid_face.setEnabled(enabled)

        self.chk_crop.toggled.connect(update_crop_widgets)

        # Face cropping option
        self.chk_avoid_face = QCheckBox("Avoid face cropping")
        self.chk_avoid_face.setChecked(True)
        vb_opts.addWidget(self.chk_avoid_face)

        # Initial state
        update_crop_widgets()

        # Adjustments
        adj_box = QGroupBox("Adjustments")
        root.addWidget(adj_box)
        vb_adj = QVBoxLayout(adj_box)

        # ---- Rotation (-90, 0, 90, 180 degrees) ----
        rot_row = QHBoxLayout()
        self.rot_enable = QCheckBox("Enable")
        self.rot_enable.setChecked(True)
        self.rot_slider = QSlider(Qt.Horizontal)
        self.rot_slider.setRange(0, 3)  # 0: -90, 1: 0, 2: 90, 3: 180
        self.rot_slider.setValue(2)  # Default to 90 degrees
        self.rot_val_lbl = QLabel("90°")
        self.rot_default_btn = QPushButton("Default")
        self.rot_default_btn.clicked.connect(lambda: self.rot_slider.setValue(2))  # 90°

        # Map slider values to degrees
        def update_rot_lbl(val):
            degrees = [-90, 0, 90, 180][val]
            self.rot_val_lbl.setText(f"{degrees}°")

        self.rot_slider.valueChanged.connect(update_rot_lbl)

        rot_row.addWidget(self.rot_enable)
        rot_row.addWidget(QLabel("Rotation"))
        rot_row.addWidget(self.rot_slider, 1)
        rot_row.addWidget(self.rot_val_lbl)
        rot_row.addWidget(self.rot_default_btn)
        vb_adj.addLayout(rot_row)

        self.rot_enable.toggled.connect(lambda on: self._set_row_enabled(on, [self.rot_slider, self.rot_default_btn]))

        # ---- Exposure (0.00..20.00 mapped to 0..2000) ----
        exp_row = QHBoxLayout()
        self.exp_enable = QCheckBox("Enable")
        self.exp_enable.setChecked(True)
        self.exp_slider = QSlider(Qt.Horizontal)
        self.exp_slider.setRange(0, 2000)
        self.exp_slider.setValue(int(constants.DEFAULT_EXPOSURE * 100))
        self.exp_val_lbl = QLabel(f"{constants.DEFAULT_EXPOSURE:.2f}")
        self.exp_default_btn = QPushButton("Default")
        self.exp_default_btn.clicked.connect(lambda: self.exp_slider.setValue(int(constants.DEFAULT_EXPOSURE * 100)))
        self.exp_slider.valueChanged.connect(self._update_exposure_lbl)

        exp_row.addWidget(self.exp_enable)
        exp_row.addWidget(QLabel("Exposure (×)"))
        exp_row.addWidget(self.exp_slider, 1)
        exp_row.addWidget(self.exp_val_lbl)
        exp_row.addWidget(self.exp_default_btn)
        vb_adj.addLayout(exp_row)

        self.exp_enable.toggled.connect(lambda on: self._set_row_enabled(on, [self.exp_slider, self.exp_default_btn]))

        # ---- Saturation (0..100 -> ×/100) ----
        sat_row = QHBoxLayout()
        self.sat_enable = QCheckBox("Enable")
        self.sat_enable.setChecked(True)
        self.sat_slider = QSlider(Qt.Horizontal)
        self.sat_slider.setRange(100, 400)
        self.sat_slider.setValue(constants.DEFAULT_SATURATION)
        self.sat_val_lbl = QLabel(str(constants.DEFAULT_SATURATION))
        self.sat_default_btn = QPushButton("Default")
        self.sat_default_btn.clicked.connect(lambda: self.sat_slider.setValue(constants.DEFAULT_SATURATION))
        self.sat_slider.valueChanged.connect(lambda v: self.sat_val_lbl.setText(str(v)))

        sat_row.addWidget(self.sat_enable)
        sat_row.addWidget(QLabel("Saturation (0-100 → ×/100)"))
        sat_row.addWidget(self.sat_slider, 1)
        sat_row.addWidget(self.sat_val_lbl)
        sat_row.addWidget(self.sat_default_btn)
        vb_adj.addLayout(sat_row)

        self.sat_enable.toggled.connect(lambda on: self._set_row_enabled(on, [self.sat_slider, self.sat_default_btn]))

        # ---- Contrast (0..300 -> ×/100) ----
        ctr_row = QHBoxLayout()
        self.ctr_enable = QCheckBox("Enable")
        self.ctr_enable.setChecked(True)
        self.ctr_slider = QSlider(Qt.Horizontal)
        self.ctr_slider.setRange(0, 300)
        self.ctr_slider.setValue(constants.DEFAULT_CONTRAST)
        self.ctr_val_lbl = QLabel(str(constants.DEFAULT_CONTRAST))
        self.ctr_default_btn = QPushButton("Default")
        self.ctr_default_btn.clicked.connect(lambda: self.ctr_slider.setValue(constants.DEFAULT_CONTRAST))
        self.ctr_slider.valueChanged.connect(lambda v: self.ctr_val_lbl.setText(str(v)))

        ctr_row.addWidget(self.ctr_enable)
        ctr_row.addWidget(QLabel("Contrast (0-300 → ×/100)"))
        ctr_row.addWidget(self.ctr_slider, 1)
        ctr_row.addWidget(self.ctr_val_lbl)
        ctr_row.addWidget(self.ctr_default_btn)
        vb_adj.addLayout(ctr_row)

        self.ctr_enable.toggled.connect(lambda on: self._set_row_enabled(on, [self.ctr_slider, self.ctr_default_btn]))

        # ---- JPEG quality (0..100) ----
        q_row = QHBoxLayout()
        self.q_slider = QSlider(Qt.Horizontal)
        self.q_slider.setRange(0, 100)
        self.q_slider.setValue(constants.DEFAULT_JPEG_QUALITY)
        self.q_val_lbl = QLabel(str(constants.DEFAULT_JPEG_QUALITY))
        self.q_default_btn = QPushButton("Default")
        self.q_default_btn.clicked.connect(lambda: self.q_slider.setValue(constants.DEFAULT_JPEG_QUALITY))
        self.q_slider.valueChanged.connect(lambda v: self.q_val_lbl.setText(str(v)))

        q_row.addWidget(QLabel("JPEG Quality (%)"))
        q_row.addWidget(self.q_slider, 1)
        q_row.addWidget(self.q_val_lbl)
        q_row.addWidget(self.q_default_btn)
        vb_adj.addLayout(q_row)

        # Actions
        actions_row = QHBoxLayout()
        root.addLayout(actions_row)
        self.run_btn = QPushButton("Process images")
        self.run_btn.clicked.connect(self.on_run)
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.on_stop)
        actions_row.addWidget(self.run_btn)
        actions_row.addWidget(self.stop_btn)

        # Log
        log_box = QGroupBox("Log")
        root.addWidget(log_box, 1)
        vb_log = QVBoxLayout(log_box)
        self.log_edit = QTextEdit()
        self.log_edit.setReadOnly(True)
        vb_log.addWidget(self.log_edit, 1)
        self.status_lbl = QLabel("Ready.")
        vb_log.addWidget(self.status_lbl)

        # Initialize labels
        self._update_exposure_lbl(self.exp_slider.value())

    # ---- UI helpers ----

    def _set_row_enabled(self, on: bool, widgets: List[QWidget]):
        """Enable/disable a set of widgets based on a checkbox state."""
        for w in widgets:
            w.setEnabled(on)

    def _update_exposure_lbl(self, slider_val: int):
        """Update exposure label from slider value (0..2000 -> 0.00..20.00)."""
        factor = slider_val / 100.0
        self.exp_val_lbl.setText(f"{factor:.2f}")

    def append_log(self, msg: str):
        """Append a line to the log text panel."""
        self.log_edit.append(msg)
        cursor = self.log_edit.textCursor()
        self.log_edit.setTextCursor(cursor)

    # ---- Actions ----

    def on_browse(self):
        """Open a directory chooser and update the folder line edit."""
        start_dir = self.folder_edit.text() or str(helper.get_script_dir())
        chosen = QFileDialog.getExistingDirectory(self, "Choose folder", start_dir)
        if chosen:
            self.folder_edit.setText(chosen)

    def on_run(self):
        """Start background processing thread with current UI settings."""
        folder = Path(self.folder_edit.text()).expanduser().resolve()
        if not folder.exists() or not folder.is_dir():
            self.append_log("Error: The selected folder is invalid.")
            self.status_lbl.setText("Error: invalid folder.")
            return

        # Build a params template from current UI state (no paths yet)
        rotation_angles = [-90, 0, 90, 180]
        params = params_class.ProcessingParams(
            rotation_angle=rotation_angles[self.rot_slider.value()] if self.rot_enable.isChecked() else 0,
            crop_kobo=self.chk_crop.isChecked(),
            crop_width=self.crop_width.value(),
            crop_height=self.crop_height.value(),
            avoid_face_cropping=self.chk_avoid_face.isChecked(),
            exposure_factor=self.exp_slider.value() / 100.0,
            saturation_val=self.sat_slider.value(),
            contrast_val=self.ctr_slider.value(),
            jpg_quality=self.q_slider.value(),
            use_exposure=self.exp_enable.isChecked(),
            use_saturation=self.sat_enable.isChecked(),
            use_contrast=self.ctr_enable.isChecked(),
        )

        # Spin up worker thread
        self.thread = QThread(self)
        self.worker = worker_class.BatchWorker(folder, params)
        self.worker.moveToThread(self.thread)

        # Connect signals/slots
        self.thread.started.connect(self.worker.run)
        self.worker.log_msg.connect(self.append_log)
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_finished)
        self.thread.finished.connect(self.thread.deleteLater)

        # Update UI state
        self.run_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_lbl.setText("Processing…")
        self.append_log("Starting…")

        # Start
        self.thread.start()

    def on_stop(self):
        """Request stop; the worker checks a flag between files."""
        if self.worker:
            self.worker.stop()
            self.append_log("Stop requested…")
        self.stop_btn.setEnabled(False)

    def on_progress(self, processed: int, total: int):
        """Update status during batch run."""
        self.status_lbl.setText(f"Processing… {processed}/{total}")

    def on_finished(self, processed: int, errors: int):
        """Cleanup after batch run and restore UI."""
        self.append_log(f"Done. Processed: {processed}, Errors: {errors}")
        self.status_lbl.setText(f"Done. Processed: {processed}, Errors: {errors}")
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

        # Ensure thread stops
        if self.thread and self.thread.isRunning():
            self.thread.quit()
            self.thread.wait()
        self.thread = None
        self.worker = None
