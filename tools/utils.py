import os
import subprocess
import logging

# 导入错误处理机制
from exceptions import ValidationError, ErrorHandler

# 日志配置移除（避免重复配置）
# logging.basicConfig 已在主程序中配置

# 初始化错误处理器
error_handler = ErrorHandler()
logger = logging.getLogger(__name__)


def execute_command(command, args=None, cwd=None, shell=False, check=True):
    """Executes a system command and returns its output.

    Args:
        command (str): The command to execute.
        args (list, optional): A list of arguments for the command. Defaults to None.
        cwd (str, optional): The working directory for the command. Defaults to None.
        shell (bool, optional): Whether to use the shell to execute the command.
                           Defaults to False.
                           SECURITY WARNING: Using shell=True can be a security
                           hazard if command or args are constructed from external
                           input. Use with caution.
        check (bool, optional): If True, raises a CalledProcessError if the
                                command returns a non-zero exit code.
                                Defaults to True.

    Returns:
        subprocess.CompletedProcess: The result of the command execution.

    Raises:
        subprocess.CalledProcessError: If the command returns a non-zero exit
                                       code and check is True.
        FileNotFoundError: If the command is not found.
        Exception: For other potential errors during command execution.
    """
    if args is None:
        args = []

    command_list = [command] + args
    logging.info(
        f"Executing command: {
            ' '.join(command_list)} in {
            cwd or os.getcwd()}"
    )

    try:
        result = subprocess.run(
            command_list,
            capture_output=True,
            text=True,
            cwd=cwd,
            shell=shell,
            check=check,  # This will raise CalledProcessError for non-zero exit codes
        )
        logging.info(f"Command executed successfully. STDOUT: {result.stdout[:200]}...")
        if result.stderr:
            logging.warning(f"Command STDERR: {result.stderr[:200]}...")
        return result
    except subprocess.CalledProcessError as e:
        logging.error(
            f"Command '{' '.join(command_list)}' failed with exit code "
            f"{e.returncode}."
        )
        logging.error(f"STDOUT: {e.stdout}")
        logging.error(f"STDERR: {e.stderr}")
        raise
    except FileNotFoundError:
        logging.error(
            f"Command '{command}' not found. Please check if it's "
            "installed and in PATH."
        )
        raise
    except Exception as e:
        logging.error(
            f"An unexpected error occurred while executing command '{command}': {e}"
        )
        raise


def get_project_root(marker_filename="project_config.yaml"):
    """Gets the absolute path to the project's root directory.

    Identifies the root by searching upwards from the current file's directory
    for a '.git' directory or a specific marker file (e.g., 'project_config.yaml').

    Args:
        marker_filename (str, optional): The name of a marker file to look for.
                                         Defaults to "project_config.yaml".

    Returns:
        str: The absolute path to the project root directory.

    Raises:
        FileNotFoundError: If the project root cannot be determined.
    """
    current_path = os.path.abspath(os.path.dirname(__file__))
    # Attempt to find project root by looking for .git or marker_filename
    # The script is in tools, so project root is one level up if no other markers found.
    # Default to parent of current file's directory if other checks fail.
    project_root_candidate = os.path.abspath(os.path.join(current_path, ".."))

    # Search upwards from the script's directory
    search_path = current_path
    while True:
        # Check for .git directory
        if os.path.isdir(os.path.join(search_path, ".git")):
            logging.info(
                f"Project root found at '{search_path}' (contains .git directory)."
            )
            return search_path

        # Check for marker file in 'docs/03-管理/' relative to current search_path
        # This is specific to the current project structure for project_config.yaml
        # For a truly generic template, this marker might be directly in the
        # root.
        potential_marker_dir = os.path.join(search_path, "docs", "03-管理")
        if os.path.isfile(os.path.join(potential_marker_dir, marker_filename)):
            logging.info(
                f"Project root found at '{search_path}' "
                f"(marker '{marker_filename}' found in 'docs/03-管理/')."
            )
            return search_path

        # Check for marker file directly in the current search_path (more
        # generic)
        if os.path.isfile(os.path.join(search_path, marker_filename)):
            logging.info(
                f"Project root found at '{search_path}' "
                f"(marker '{marker_filename}' found)."
            )
            return search_path

        parent_path = os.path.dirname(search_path)
        if parent_path == search_path:
            # Reached the filesystem root
            logging.warning(
                f"Could not determine project root by .git or marker file "
                f"'{marker_filename}'. Falling back to default: "
                f"'{project_root_candidate}' (parent of utils.py)."
            )
            # Before returning the fallback, ensure it's a plausible project structure
            # For example, check if 'tools' and 'docs' subdirectories exist
            if os.path.isdir(
                os.path.join(project_root_candidate, "tools")
            ) and os.path.isdir(os.path.join(project_root_candidate, "docs")):
                return project_root_candidate
            else:
                logging.error(
                    f"Fallback project root '{project_root_candidate}' "
                    "does not seem to be a valid project structure. "
                    "(Missing 'tools' or 'docs' "
                    "directories)."
                )
                raise FileNotFoundError(
                    "Project root could not be determined. Ensure the script is "
                    "run from within the project, or that a '.git' directory or "
                    "marker file (e.g., 'project_config.yaml') exists in the root."
                )
        search_path = parent_path


def ensure_dir_exists(dir_path):
    """Ensures that a directory exists, creating it if necessary.

    Args:
        dir_path (str): The path to the directory.

    Returns:
        bool: True if the directory exists or was created, False otherwise.
    """
    try:
        os.makedirs(dir_path, exist_ok=True)
        logging.info(f"Directory '{dir_path}' ensured.")
        return True
    except OSError as e:
        logging.error(f"Error creating directory '{dir_path}': {e}")
        return False


if __name__ == "__main__":
    # Example usage (optional, for testing the module directly)
    try:
        logger.info(f"Project Root: {get_project_root()}")

        test_dir = os.path.join(get_project_root(), "temp_test_dir_utils")
        logger.info(f"Ensuring directory exists: {test_dir}")
        ensure_dir_exists(test_dir)

        logger.info(f"Listing contents of {get_project_root()}:")
        try:
            # Example: list files in the project root (use a safe command)
            # On Windows, 'dir' is a shell command. On Linux/macOS, 'ls' is
            # an executable.
            if os.name == "nt":  # Windows
                # 'dir' is a shell built-in, so shell=True is often needed
                # or use 'cmd /c dir'
                # However, to avoid shell=True, we can try to find a common executable.
                # For simplicity, let's assume a common command like 'git status'
                # might work if git is installed.
                # Or, we can just skip this part in the example if it's too
                # complex for a simple demo.
                # result = execute_command(
                # "cmd", args=["/c", "dir"], cwd=get_project_root()
                # )
                logger.info(
                    "(Skipping directory listing example on Windows for simplicity in "
                    "__main__)"
                )
            else:  # Linux/macOS
                result = execute_command("ls", args=["-la"], cwd=get_project_root())
                logger.info(result.stdout)
        except Exception as e:
            error_handler.handle_error(
                ValidationError(f"Error executing command for example: {e}")
            )

        # Clean up the test directory
        if os.path.exists(test_dir):
            try:
                os.rmdir(test_dir)  # rmdir only works on empty directories
                logger.info(f"Cleaned up test directory: {test_dir}")
            except OSError as e:
                logger.warning(
                    f"Could not remove test directory {test_dir}: {e}. "
                    "It might not be empty or permission issues."
                )
    except Exception as e:
        error_handler.handle_error(ValidationError(f"Utils module test failed: {e}"))
