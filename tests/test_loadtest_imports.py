import importlib.util
import sys
from pathlib import Path
from types import ModuleType


def test_locustfile_imports_stop_test_from_locust_exception(monkeypatch):
    class HttpUser:
        pass

    class StopTest(Exception):
        pass

    locust = ModuleType("locust")
    locust.__path__ = []
    locust.HttpUser = HttpUser
    locust.between = lambda *_args: None
    locust.task = lambda function: function

    locust_exception = ModuleType("locust.exception")
    locust_exception.StopTest = StopTest
    monkeypatch.setitem(sys.modules, "locust", locust)
    monkeypatch.setitem(sys.modules, "locust.exception", locust_exception)

    path = Path(__file__).resolve().parents[1] / "loadtest" / "locustfile.py"
    spec = importlib.util.spec_from_file_location("parking_loadtest_locustfile", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)

    spec.loader.exec_module(module)

    assert module.StopTest is StopTest
    assert issubclass(module.GateParkingUser, HttpUser)
