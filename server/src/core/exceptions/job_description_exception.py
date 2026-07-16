class JobDescriptionBaseException(Exception):
    """Base for all job description related exceptions."""

    def __init__(
        self,
        message: str,
        details: str | None = None,
        error_code: str | None = None,
        status_code: int = 400,
    ):
        self.message = message
        self.details = details
        self.error_code = error_code
        self.status_code = status_code

        super().__init__(self.message)


class InvalidEmploymentType(JobDescriptionBaseException):
    def __init__(
        self,
        details: str | None = None,
        error_code: str | None = None,
    ):
        super().__init__(
            message="Invalid employment type",
            details=details,
            error_code=error_code,
        )

class InvalidJobDescriptionStatus(JobDescriptionBaseException):
    def __init__(
        self,
        details: str | None = None,
        error_code: str | None = None,
    ):
        super().__init__(
            message="Invalid job description status",
            details=details,
            error_code=error_code,
        )

class RecruiterAccessRequired(JobDescriptionBaseException):
    def __init__(
        self,
        details: str | None = None,
        error_code: str | None = None,
    ):
        super().__init__(
            message="Recruiter access required",
            details=details,
            error_code=error_code,
        )

class JobDescriptionNotFound(
    JobDescriptionBaseException
):
    def __init__(
        self,
        details: str | None = None,
        error_code: str | None = None,
    ):
        super().__init__(
            message="Job description not found",
            details=details,
            error_code=error_code,
        )

class JobDescriptionScoringInProgress(JobDescriptionBaseException):
    def __init__(
        self,
        details: str | None = None,
        error_code: str | None = None,
    ):
        super().__init__(
            message="This Job Description cannot be edited while candidate scoring is in progress.",
            details=details,
            error_code=error_code or "SCORING_IN_PROGRESS",
            status_code=409,
        )
