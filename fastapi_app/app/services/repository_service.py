"""
File I/O and repository management services.
"""
import git
import os
from github import Github, GithubException
from pathlib import Path
from typing import Dict, List, Optional

from ..core import logger, ensure_directory, is_code_file
from ..core.config import settings

class RepositoryService:
    """Service for managing homework repository structure."""

    def __init__(self, homework_dir: Optional[Path] = None):
        # The base path is configurable via an environment variable for Lambda (e.g., /mnt/efs)
        self.base_storage_path = Path(os.environ.get("STORAGE_PATH", settings.homework_dir))
        self.homework_dir = self.base_storage_path
        self.github_repos_path = self.base_storage_path / "github_repos"
        ensure_directory(self.homework_dir)
        ensure_directory(self.github_repos_path)

    def get_homework_from_github(self, github_nickname: str, lecture_number: int) -> Path:
        """
        Clones or pulls a student's homework repository from GitHub into the EFS storage path.
        """
        try:
            # For Lambda, set GITHUB_TOKEN as an environment variable
            g = Github(os.environ.get("GITHUB_TOKEN"))
            user = g.get_user(github_nickname)
            repo_name = f"lecture_{lecture_number}"
            repo = user.get_repo(repo_name)
            clone_url = repo.clone_url

            clone_dir = self.github_repos_path / github_nickname / repo_name
            ensure_directory(clone_dir)

            if (clone_dir / ".git").exists():
                logger.info(f"Pulling latest changes for {github_nickname}/{repo_name}.")
                git.Repo(clone_dir).remotes.origin.pull()
            else:
                logger.info(f"Cloning repository for {github_nickname} into {clone_dir}")
                git.Repo.clone_from(clone_url, clone_dir)

            logger.info(f"Successfully cloned/updated repository for {github_nickname}")
            return clone_dir

        except GithubException as e:
            logger.error(f"GitHub error for {github_nickname}: {e.status} - {e.data}")
            raise ValueError(f"Could not find repository '{repo_name}' for user '{github_nickname}'.")
        except Exception as e:
            logger.error(f"Failed to get repository for {github_nickname}: {e}")
            raise

    def get_lecture_tasks(self, lecture_number: int, base_path: Optional[Path] = None) -> List[str]:
        """
        Get all task directories for a specific lecture from a given base path.
        """
        base_path = base_path or self.homework_dir
        task_dirs = []

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
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    relative_path = file_path.relative_to(task_path)
                    code_content[str(relative_path)] = content
                except Exception as e:
                    logger.warning(f"Failed to read file {file_path}: {e}")
                    relative_path = file_path.relative_to(task_path)
                    code_content[str(relative_path)] = f"Error reading file: {e}"
        return code_content

