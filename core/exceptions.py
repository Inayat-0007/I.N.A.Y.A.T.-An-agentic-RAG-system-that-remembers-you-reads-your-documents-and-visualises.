"""Domain-specific exceptions for failure-mode handling."""


class IndexBuildInProgress(Exception):
    """Raised when a second index build is requested while one is running."""

    def __init__(self, job_id: str, user_id: str) -> None:
        self.job_id = job_id
        self.user_id = user_id
        super().__init__(
            f"Index build already in progress for user '{user_id}' (job_id={job_id})."
        )
