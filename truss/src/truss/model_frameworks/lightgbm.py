from pathlib import Path
from typing import Any, Dict, Set

from truss.core.constants import LIGHTGBM_REQ_MODULE_NAMES
from truss.model_framework import ModelFramework
from truss.templates.shared.util import model_supports_predict_proba
from truss.core.types import ModelFrameworkType

MODEL_FILENAME = "model.joblib"


class LightGBM(ModelFramework):
    def typ(self) -> ModelFrameworkType:
        return ModelFrameworkType.LIGHTGBM

    def required_python_depedencies(self) -> Set[str]:
        return LIGHTGBM_REQ_MODULE_NAMES

    def serialize_model_to_directory(self, model, target_directory: Path):
        import joblib

        model_filename = MODEL_FILENAME
        model_filepath = target_directory / model_filename
        joblib.dump(model, model_filepath, compress=True)

    def model_metadata(self, model) -> Dict[str, Any]:
        supports_predict_proba = model_supports_predict_proba(model)
        return {
            "model_binary_dir": "model",
            "supports_predict_proba": supports_predict_proba,
        }

    def supports_model_class(self, model_class) -> bool:
        model_framework, _, _ = model_class.__module__.partition(".")
        return model_framework == ModelFrameworkType.LIGHTGBM.value