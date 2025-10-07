import orc
import unittest


class TestOrchestrator(unittest.TestCase):

    def test_another_feature(self):
        """Test another feature."""
        result = orc.orchestrator.print_version()
        self.assertTrue(result == "Orkestry version 0.1")

if __name__ == '__main__':
    unittest.main()
