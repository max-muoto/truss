import time
from typing import Any, Dict, List


class Model:
    def __init__(self, **kwargs) -> None:
        self._data_dir = kwargs["data_dir"]
        self._config = kwargs["config"]
        self._secrets = kwargs["secrets"]
        self._model = None

    def load(self):
        # Load model here and assign to self._model.
        print("hello")
        pass

    def predict(self, model_input: Any) -> Dict[str, List]:
        # Invoke model on model_input and calculate predictions here.
        print("hello from concurrency truss")
        time.sleep(2)
        return model_input
