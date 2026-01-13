from pathlib import Path
import json
from dataclasses import asdict, is_dataclass
from typing import Dict, Any

from src import params_class
from src import helper


CONFIG_FILENAME = "EbookImageOptimiser_Config.json"


def _config_path() -> Path:
    """Return the full path to the config file."""
    return helper.get_script_dir() / CONFIG_FILENAME


class PresetManager:
    """Manages loading and saving of processing presets."""

    @staticmethod
    def collect_params_from_ui(ui) -> params_class.ProcessingParams:
        """Build a ProcessingParams from UI state."""
        rotation_angles = [-90, 0, 90, 180]
        return params_class.ProcessingParams(
            rotation_angle=rotation_angles[ui.rot_slider.value()] if ui.rot_enable.isChecked() else 0,
            crop_kobo=ui.chk_crop.isChecked(),
            crop_width=ui.crop_width.value(),
            crop_height=ui.crop_height.value(),
            avoid_face_cropping=ui.chk_avoid_face.isChecked(),
            exposure_factor=ui.exp_slider.value() / 100.0,
            saturation_val=ui.sat_slider.value(),
            contrast_val=ui.ctr_slider.value(),
            jpg_quality=ui.q_slider.value(),
            use_exposure=ui.exp_enable.isChecked(),
            use_saturation=ui.sat_enable.isChecked(),
            use_contrast=ui.ctr_enable.isChecked(),
        )

    @staticmethod
    def apply_params_to_ui(ui, data: Dict[str, Any]) -> None:
        """Apply a dict of ProcessingParams fields back to the UI."""
        # Safe defaults: use the current widget values as fallbacks
        rotation_angles = [-90, 0, 90, 180]
        angle = int(data.get("rotation_angle", 0))
        idx = rotation_angles.index(angle) if angle in rotation_angles else 1  # default to 0°
        ui.rot_enable.setChecked(angle != 0)
        ui.rot_slider.setValue(idx)

        ui.chk_crop.setChecked(bool(data.get("crop_kobo", ui.chk_crop.isChecked())))
        ui.crop_width.setValue(int(data.get("crop_width", ui.crop_width.value())))
        ui.crop_height.setValue(int(data.get("crop_height", ui.crop_height.value())))
        ui.chk_avoid_face.setChecked(bool(data.get("avoid_face_cropping", ui.chk_avoid_face.isChecked())))

        ui.exp_enable.setChecked(bool(data.get("use_exposure", ui.exp_enable.isChecked())))
        ui.exp_slider.setValue(int(round(float(data.get("exposure_factor", ui.exp_slider.value() / 100.0)) * 100)))
        ui._update_exposure_lbl(ui.exp_slider.value())

        ui.sat_enable.setChecked(bool(data.get("use_saturation", ui.sat_enable.isChecked())))
        ui.sat_slider.setValue(int(data.get("saturation_val", ui.sat_slider.value())))

        ui.ctr_enable.setChecked(bool(data.get("use_contrast", ui.ctr_enable.isChecked())))
        ui.ctr_slider.setValue(int(data.get("contrast_val", ui.ctr_slider.value())))

        ui.q_slider.setValue(int(data.get("jpg_quality", ui.q_slider.value())))

    @staticmethod
    def save_default(ui) -> None:
        """
        Serialize all fields from ProcessingParams to JSON in the app directory.
        Filename: EbookImageOptimiser_Config.json
        """
        def default_serializer(obj):
            if isinstance(obj, Path):
                return str(obj)
            raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

        try:
            params = PresetManager.collect_params_from_ui(ui)

            # Export robustly whether ProcessingParams is a @dataclass or a normal class
            if is_dataclass(params):
                data = asdict(params, dict_factory=lambda x: {k: v for k, v in x if v is not None})
            else:
                data = {k: v for k, v in vars(params).items() if v is not None}

            cfg_path = _config_path()
            with cfg_path.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=default_serializer)
            ui.append_log(f"Saved defaults to: {cfg_path}")
            ui.status_lbl.setText("Defaults saved.")
        except Exception as e:
            ui.append_log(f"Error saving defaults: {e}")
            ui.status_lbl.setText("Error saving defaults.")

    @staticmethod
    def load_default_settings(ui) -> None:
        """
        If a config JSON exists next to the EXE (or project root when not frozen),
        load it and apply values to the UI.
        """
        try:
            cfg_path = _config_path()
            if not cfg_path.exists():
                ui.append_log("No default settings found.")
                return

            with cfg_path.open("r", encoding="utf-8") as f:
                data = json.load(f)

            # Apply to UI
            PresetManager.apply_params_to_ui(ui, data)
            ui.append_log(f"Loaded defaults from: {cfg_path}")
            ui.status_lbl.setText("Defaults loaded.")
        except Exception as e:
            ui.append_log(f"Error loading defaults: {e}")
            ui.status_lbl.setText("Error loading defaults.")
