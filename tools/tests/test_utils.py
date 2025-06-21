from utils import execute_command, get_project_root, ensure_dir_exists
import unittest
import os
import shutil
import subprocess
from pathlib import Path

# Adjust the path to import utils from the parent directory (tools)
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestUtils(unittest.TestCase):

    def setUp(self):
        """Set up for test methods."""
        self.test_dir = Path(__file__).parent / "test_temp_dir_for_utils"
        # Clean up before each test, in case a previous test failed to clean up
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        self.test_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        """Tear down after test methods."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_get_project_root(self):
        """Test the get_project_root function."""
        expected_root = Path("{{PROJECT_ROOT}}/.").resolve()
        self.assertEqual(get_project_root(), expected_root)
        # You might want to add more sophisticated tests if the logic for
        # finding root becomes complex

    def test_ensure_dir_exists_creates_new_directory(self):
        """Test ensure_dir_exists creates a directory if it doesn't exist."""
        new_dir_path = self.test_dir / "new_subdir"
        self.assertFalse(new_dir_path.exists())
        self.assertTrue(ensure_dir_exists(str(new_dir_path)))
        self.assertTrue(new_dir_path.exists())
        self.assertTrue(new_dir_path.is_dir())

    def test_ensure_dir_exists_existing_directory(self):
        """Test ensure_dir_exists does nothing if directory already exists."""
        self.assertTrue(self.test_dir.exists())  # Setup creates this
        self.assertTrue(ensure_dir_exists(str(self.test_dir)))
        self.assertTrue(self.test_dir.exists())

    def test_execute_command_success(self):
        """Test execute_command with a successful command."""
        # Using 'echo' as a simple, cross-platform command
        # (might need adjustment for pure Windows cmd vs PowerShell)
        # For Windows, 'cmd /c echo' is safer if not using shell=True
        # For non-Windows, 'echo' is fine.
        if os.name == "nt":
            result = execute_command(
                "cmd", args=["/c", "echo", "hello world"], check=True
            )
        else:
            result = execute_command("echo", args=["hello world"], check=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn("hello world", result.stdout)

    def test_execute_command_failure(self):
        """Test execute_command with a failing command."""
        # Command that is likely to fail (e.g., non-existent command or command
        # with error exit code)
        with self.assertRaises(subprocess.CalledProcessError):
            if os.name == "nt":
                # Example: 'exit 1' to force an error
                execute_command("cmd", args=["/c", "exit", "1"], check=True)
            else:
                execute_command(
                    "false", check=True
                )  # 'false' command exists on Unix-like systems and returns 1

    def test_execute_command_file_not_found(self):
        """Test execute_command with a non-existent command."""
        with self.assertRaises(FileNotFoundError):
            execute_command("non_existent_command_gfdhsjfgd", check=True)

    def test_execute_command_cwd(self):
        """Test execute_command with a specific current working directory."""
        # Create a dummy file in the test_dir to check if cwd works
        dummy_file_path = self.test_dir / "test_file_for_cwd.txt"
        with open(dummy_file_path, "w") as f:
            f.write("test content")

        self.assertTrue(dummy_file_path.exists())

        if os.name == "nt":
            # 'type' command on Windows to display file content
            result = execute_command(
                "cmd",
                args=["/c", "type", "test_file_for_cwd.txt"],
                cwd=str(self.test_dir),
                check=True,
            )
            self.assertIn("test content", result.stdout)
            # Check that the command fails if run from a different CWD without
            # specifying the path
            with self.assertRaises(subprocess.CalledProcessError):
                execute_command(
                    "cmd",
                    args=["/c", "type", "test_file_for_cwd.txt"],
                    cwd=str(Path(__file__).parent),
                    check=True,
                )
        else:
            # 'cat' command on Unix-like systems
            result = execute_command(
                "cat",
                args=["test_file_for_cwd.txt"],
                cwd=str(self.test_dir),
                check=True,
            )
            self.assertIn("test content", result.stdout)
            # Check that the command fails if run from a different CWD without
            # specifying the path
            with self.assertRaises(subprocess.CalledProcessError):
                # 'cat' will error if file not found, which is what we expect here
                execute_command(
                    "cat",
                    args=["test_file_for_cwd.txt"],
                    cwd=str(Path(__file__).parent),
                    check=True,
                )

    def test_ensure_dir_exists_error_creating(self):
        """Test ensure_dir_exists when os.makedirs raises an OSError.

        E.g., permission denied.
        """
        # This is hard to test reliably without actually changing
        # file system permissions,
        # which is risky. We can mock os.makedirs to simulate the error.
        original_makedirs = os.makedirs

        def mock_makedirs(path, exist_ok=False):
            if str(path).endswith("uncreatable_dir"):
                raise OSError("Simulated permission denied")
            return original_makedirs(path, exist_ok=exist_ok)

        os.makedirs = mock_makedirs
        uncreatable_path = self.test_dir / "uncreatable_dir"
        self.assertFalse(ensure_dir_exists(str(uncreatable_path)))
        self.assertFalse(uncreatable_path.exists())
        os.makedirs = original_makedirs  # Restore original function


if __name__ == "__main__":
    unittest.main()
