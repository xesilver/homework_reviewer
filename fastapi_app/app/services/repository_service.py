import git
import os
import shutil
import stat
from github import Github, GithubException
from pathlib import Path
from typing import Dict, List, Optional
import tempfile

from ..core import logger, is_code_file

# --- NEW: Error handler for shutil.rmtree on Windows ---
# This function helps delete files that git marks as read-only.
def remove_readonly(func, path, exc_info):
    """
    Error handler for shutil.rmtree.

    If the error is due to an access error (read only file)
    it attempts to add write permission and then retries.

    If the error is for another reason it re-raises the error.
    """
    if not os.access(path, os.W_OK):
        # Is the error an access error ?
        os.chmod(path, stat.S_IWUSR)
        func(path)
    else:
        raise

class RepositoryService:
    """Service for managing homework repository structure."""

    def __init__(self, homework_dir: Optional[Path] = None):
        self.base_storage_path = Path(tempfile.gettempdir())
        self.github_repos_path = self.base_storage_path / "github_repos"
        self.github_repos_path.mkdir(exist_ok=True)


    def get_homework_from_github(self, github_nickname: str, lecture_number: int) -> Path:
        """
        Clones a student's homework repository from GitHub into a temporary directory.
        """
        clone_dir = self.github_repos_path / github_nickname / f"lecture_{lecture_number}"
        
        try:
            # If the directory exists from a previous failed run, remove it robustly.
            if clone_dir.exists():
                shutil.rmtree(clone_dir, onerror=remove_readonly)
            
            clone_dir.mkdir(parents=True, exist_ok=True)

            g = Github(os.environ.get("GITHUB_TOKEN"))
            user = g.get_user(github_nickname)
            repo_name = f"lecture_{lecture_number}"
            repo = user.get_repo(repo_name)
            
            logger.info(f"Cloning repository for {github_nickname} into temporary directory: {clone_dir}")
            git.Repo.clone_from(repo.clone_url, clone_dir)
            logger.info(f"Successfully cloned repository for {github_nickname}")
            
            return clone_dir

        except Exception as e:
            logger.error(f"Failed to get repository for {github_nickname}: {e}")
            raise

    def cleanup_repository(self, repo_path: Path):
        """
        Deletes the parent directory of the cloned repository (the user's folder).
        """
        user_folder = repo_path.parent
        if user_folder and user_folder.exists():
            try:
                # Use the robust error handler for cleanup as well
                shutil.rmtree(user_folder, onerror=remove_readonly)
                logger.info(f"Successfully cleaned up temporary directory: {user_folder}")
            except Exception as e:
                logger.error(f"Failed to clean up temporary directory {user_folder}: {e}")

    def get_lecture_tasks(self, lecture_number: int, base_path: Optional[Path] = None) -> List[str]:
        task_dirs = []
        if not base_path or not base_path.exists():
            return task_dirs
            
        for item in base_path.iterdir():
            if item.is_dir() and item.name.startswith("task_"):
                task_dirs.append(item.name)

        return sorted(task_dirs)

    def read_code_from_path(self, task_path: Path) -> Dict[str, str]:
        """Reads all code files from a given task path."""
        code_content = {}
        if not task_path.exists() or not task_path.is_dir():
            return code_content

        for file_path in task_path.rglob("*"):
            if file_path.is_file() and is_code_file(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    relative_path = file_path.relative_to(task_path)
                    code_content[str(relative_path)] = content
                except Exception as e:
                    logger.warning(f"Failed to read file {file_path}: {e}")
                    relative_path = file_path.relative_to(task_path)
                    code_content[str(relative_path)] = f"Error reading file: {e}"
        return code_content