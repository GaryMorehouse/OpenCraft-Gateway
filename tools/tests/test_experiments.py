import unittest

from . import _pathfix  # noqa: F401

from smartcraft_toolkit.experiments import EXPERIMENTS


class TestExperimentManifest(unittest.TestCase):
    def test_every_registered_log_path_exists(self):
        for exp in EXPERIMENTS:
            self.assertTrue(exp.path.is_file(), f"{exp.name}: missing log file {exp.path}")

    def test_continuous_experiments_have_no_single_rpm_rank(self):
        for exp in EXPERIMENTS:
            if "continuous" in exp.tags:
                self.assertIsNone(
                    exp.rpm_rank,
                    f"{exp.name}: tagged 'continuous' but has an rpm_rank -- "
                    "a session spanning multiple conditions shouldn't claim one steady rank",
                )


if __name__ == "__main__":
    unittest.main()
