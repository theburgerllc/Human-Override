import unittest
from pathlib import Path
import yaml

from tools.tho import validate_episode


class TestValidate(unittest.TestCase):
    def test_ep01_valid(self):
        root = Path(__file__).resolve().parent.parent
        ep = root / "episodes" / "season01_housing_mode" / "ep01.yaml"
        data = yaml.safe_load(ep.read_text(encoding="utf-8"))
        validate_episode(data, context=str(ep))


if __name__ == "__main__":
    unittest.main()
