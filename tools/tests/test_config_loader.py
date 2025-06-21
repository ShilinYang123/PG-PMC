from config_loader import get_config, validate_config, CONFIG_FILE_PATH
import unittest
import yaml
from pathlib import Path
# import os  # Unused import

# Adjust the path to import config_loader from the parent directory (tools)
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# Helper to create a temporary config file
def create_temp_config_file(tmp_path, content):
    config_file = tmp_path / "temp_project_config.yaml"
    with open(config_file, "w", encoding="utf-8") as f:
        yaml.dump(content, f)
    return config_file


class TestConfigLoader(unittest.TestCase):

    def setUp(self):
        """Setup for test methods."""
        self.original_config_path = CONFIG_FILE_PATH
        self.test_config_dir = Path(__file__).parent / "test_config_temp"
        self.test_config_dir.mkdir(exist_ok=True)
        # Reset the global _config in config_loader to ensure fresh load for each test
        # This requires modifying the config_loader module or having a
        # reset function there.
        # For simplicity, we'll assume direct modification or that tests
        # run in separate processes.
        # A better way would be to make get_config accept a path for testing.
        # For now, we will monkeypatch CONFIG_FILE_PATH for each test that
        # needs a custom config.
        self.valid_base_config_content = {
            "project_root": "{{PROJECT_ROOT}}/.",
            "project_name": "Test Project",
            "structure_check": {
                "report_dir": "reports/structure_checks",
                "report_filename_template": "structure_report_{timestamp}.md",
                "simplified_check_enabled": True,
                "simplified_ignore_dirs": [".git", ".vscode", "__pycache__"],
                "simplified_ignore_files": [".DS_Store"],
                "simplified_max_depth": 5,
                "simplified_report_title": "Simplified Structure Check Report",
            },
            "code_quality": {},
            "workspace_cleanliness": {},
            "project_cleanup": {},
            "agent_structure_validation": {},
            "update_structure_script": {},
            "structure_compliance_check": {},
            "error_path_detection": {},
            "project_backup": {},
            "final_summary": {},
            "logging": {},
            "common_paths": {},
            "file_extensions": {},
            "ignored_patterns": [],
            "tool_specific": {},
        }

    def tearDown(self):
        """Tear down after test methods."""
        # Restore original config path for other tests or modules
        import config_loader

        config_loader.CONFIG_FILE_PATH = self.original_config_path
        config_loader._config = None  # Reset memoized config
        if self.test_config_dir.exists():
            for item in self.test_config_dir.iterdir():
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    # shutil.rmtree(item) # If subdirectories are created
                    pass
            self.test_config_dir.rmdir()  # Remove the temp dir itself if empty

    def test_validate_config_valid(self):
        """Test validate_config with a valid configuration."""
        try:
            validate_config(self.valid_base_config_content)
        except ValueError as e:
            self.fail(f"validate_config raised ValueError unexpectedly: {e}")

    def test_validate_config_missing_top_level_key(self):
        """Test validate_config with a missing required top-level key."""
        invalid_config = self.valid_base_config_content.copy()
        del invalid_config["project_name"]
        with self.assertRaisesRegex(
            ValueError, "配置文件中缺少必需的顶级键: 'project_name'"
        ):
            validate_config(invalid_config)

    def test_validate_config_incorrect_type_top_level(self):
        """Test validate_config with an incorrect type for a top-level key."""
        invalid_config = self.valid_base_config_content.copy()
        invalid_config["project_name"] = 123  # Should be string
        with self.assertRaisesRegex(
            ValueError,
            "配置键 'project_name' 的类型错误。期望: <class 'str'>, 实际: <class 'int'>",
        ):
            validate_config(invalid_config)

    def test_validate_config_project_root_path_object(self):
        """Test validate_config with project_root as a Path object."""
        config = self.valid_base_config_content.copy()
        config["project_root"] = Path("{{PROJECT_ROOT}}/.")
        try:
            validate_config(config)
        except ValueError as e:
            self.fail(
                f"validate_config raised ValueError unexpectedly for Path object: {e}")

    def test_validate_config_project_root_empty_string(self):
        """Test validate_config with project_root as an empty string.

        Should be handled by get_config default.
        """
        config = self.valid_base_config_content.copy()
        config["project_root"] = ""  # Empty string
        # validate_config itself might not raise error here if it expects
        # get_config to handle default
        # The current validate_config has a continue for this case.
        try:
            # Should pass validation as per current logic
            validate_config(config)
        except ValueError as e:
            self.fail(
                f"validate_config raised ValueError unexpectedly for "
                f"empty project_root: {e}")

    def test_get_config_default_project_root(self):
        """Test get_config sets a default project_root if not provided or empty."""
        config_content_no_root = self.valid_base_config_content.copy()
        del config_content_no_root["project_root"]  # Remove it

        temp_config_file = create_temp_config_file(
            self.test_config_dir, config_content_no_root
        )
        import config_loader

        config_loader.CONFIG_FILE_PATH = temp_config_file
        config_loader._config = None

        try:
            config = get_config()
            self.assertIsNotNone(config.get("project_root"))
            # Default is two levels up from config_loader.py's parent (tools ->
            # 3AI)
            expected_default_root = Path(
                config_loader.__file__).parent.parent.resolve()
            self.assertEqual(config["project_root"], expected_default_root)
        except Exception as e:
            self.fail(f"get_config failed to set default project_root: {e}")
        finally:
            config_loader.CONFIG_FILE_PATH = self.original_config_path
            config_loader._config = None
            if temp_config_file.exists():
                temp_config_file.unlink()

        # Test with empty project_root string
        config_content_empty_root = self.valid_base_config_content.copy()
        config_content_empty_root["project_root"] = ""
        temp_config_file_empty = create_temp_config_file(
            self.test_config_dir, config_content_empty_root
        )
        config_loader.CONFIG_FILE_PATH = temp_config_file_empty
        config_loader._config = None
        try:
            config = get_config()
            self.assertIsNotNone(config.get("project_root"))
            expected_default_root = Path(
                config_loader.__file__).parent.parent.resolve()
            self.assertEqual(config["project_root"], expected_default_root)
        except Exception as e:
            self.fail(
                f"get_config failed to set default project_root for empty string: {e}")
        finally:
            config_loader.CONFIG_FILE_PATH = self.original_config_path
            config_loader._config = None
            if temp_config_file_empty.exists():
                temp_config_file_empty.unlink()

    def test_validate_config_missing_nested_key(self):
        """Test validate_config with a missing required nested key."""
        invalid_config = self.valid_base_config_content.copy()
        invalid_config["structure_check"] = self.valid_base_config_content[
            "structure_check"
        ].copy()
        del invalid_config["structure_check"]["report_dir"]
        with self.assertRaisesRegex(
            ValueError, "配置 'structure_check' 中缺少必需的键: 'report_dir'"
        ):
            validate_config(invalid_config)

    def test_validate_config_incorrect_type_nested_key(self):
        """Test validate_config with an incorrect type for a nested key."""
        invalid_config = self.valid_base_config_content.copy()
        invalid_config["structure_check"] = self.valid_base_config_content[
            "structure_check"
        ].copy()
        invalid_config["structure_check"][
            "simplified_max_depth"
        ] = "five"  # Should be int
        with self.assertRaisesRegex(
            ValueError,
            "配置键 'structure_check.simplified_max_depth' 的类型错误。"
            "期望: <class 'int'>, 实际: <class 'str'>",
        ):
            validate_config(invalid_config)

    def test_get_config_loads_and_validates(self):
        """Test get_config successfully loads and validates a temporary config file."""
        temp_config_file = create_temp_config_file(
            self.test_config_dir, self.valid_base_config_content
        )

        import config_loader  # Re-import or access module directly for monkeypatching

        config_loader.CONFIG_FILE_PATH = temp_config_file
        config_loader._config = None  # Ensure it reloads

        try:
            config = get_config()
            self.assertIsNotNone(config)
            self.assertEqual(config["project_name"], "Test Project")
            self.assertIsInstance(config["project_root"], Path)
            self.assertEqual(
                config["project_root"],
                Path("{{PROJECT_ROOT}}/.").resolve())
            # Check a few other top-level keys for presence and type
            self.assertIn("code_quality", config)
            self.assertIsInstance(config["code_quality"], dict)
            self.assertIn("logging", config)
            self.assertIsInstance(config["logging"], dict)
        except Exception as e:
            self.fail(f"get_config failed with valid temp config: {e}")
        finally:
            # Clean up: restore original path and remove temp file
            config_loader.CONFIG_FILE_PATH = self.original_config_path
            config_loader._config = None
            if temp_config_file.exists():
                temp_config_file.unlink()

    def test_get_config_file_not_found(self):
        """Test get_config when the config file does not exist."""
        import config_loader

        non_existent_path = self.test_config_dir / "non_existent_config.yaml"
        config_loader.CONFIG_FILE_PATH = non_existent_path
        config_loader._config = None

        with self.assertRaises(FileNotFoundError):
            get_config()

        # Restore
        config_loader.CONFIG_FILE_PATH = self.original_config_path
        config_loader._config = None

    def test_get_config_invalid_yaml(self):
        """Test get_config with an invalid YAML file."""
        temp_config_file = self.test_config_dir / "invalid_config.yaml"
        with open(temp_config_file, "w", encoding="utf-8") as f:
            # Invalid YAML
            f.write("project_name: Test Project\n  bad_indent: Problem")

        import config_loader

        config_loader.CONFIG_FILE_PATH = temp_config_file
        config_loader._config = None

        with self.assertRaises(ValueError) as context:
            get_config()
        self.assertIn("配置文件格式错误", str(context.exception))

        # Restore and cleanup
        config_loader.CONFIG_FILE_PATH = self.original_config_path
        config_loader._config = None
        if temp_config_file.exists():
            temp_config_file.unlink()


if __name__ == "__main__":
    unittest.main()
