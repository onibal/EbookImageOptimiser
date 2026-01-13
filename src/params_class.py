"""
Parameter class for image processing settings.
"""

from dataclasses import dataclass, field
from pathlib import Path
from src import constants


@dataclass
class ProcessingParams:
    """
    Bundle all processing parameters in one place, with defaults.
    `in_path` and `out_path` are set per-file during the batch via `with_paths(...)`.
    """
    # IO
    in_path: Path = field(default_factory=Path)
    out_path: Path = field(default_factory=Path)

    # Options
    rotation_angle: int = 90  # 0, 90, 180, or -90 degrees
    crop_kobo: bool = True
    crop_width: int = 1680
    crop_height: int = 1264
    avoid_face_cropping: bool = True

    # Adjustments
    exposure_factor: float = constants.DEFAULT_EXPOSURE
    saturation_val: int = constants.DEFAULT_SATURATION
    contrast_val: int = constants.DEFAULT_CONTRAST
    jpg_quality: int = constants.DEFAULT_JPEG_QUALITY

    # Toggles to apply adjustments
    use_exposure: bool = True
    use_saturation: bool = True
    use_contrast: bool = True

    def with_paths(self, in_path: Path, out_path: Path) -> "ProcessingParams":
        """Return a copy of this params object with `in_path` and `out_path` set."""
        return ProcessingParams(
            in_path=in_path,
            out_path=out_path,
            rotation_angle=self.rotation_angle,
            crop_kobo=self.crop_kobo,
            avoid_face_cropping=self.avoid_face_cropping,
            exposure_factor=self.exposure_factor,
            saturation_val=self.saturation_val,
            contrast_val=self.contrast_val,
            jpg_quality=self.jpg_quality,
            use_exposure=self.use_exposure,
            use_saturation=self.use_saturation,
            use_contrast=self.use_contrast,
        )
