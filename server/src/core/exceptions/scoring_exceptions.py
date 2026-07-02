class ScoringBaseException(Exception):
    def __init__(
        self,
        message: str | None = None,
        details: str | None = None,
        error_code: str | None = None,
        status_code: int = 400,
    ):
        self.message = message
        self.details = details
        self.error_code = error_code
        self.status_code = status_code

        super().__init__(self.message)


class ResumeImportValidationError(ScoringBaseException):
    def __init__(
        self,
        details: str | None = None,
        error_code: str | None = None,
    ):
        super().__init__(
            message="Resume import validation failed",
            details=details,
            error_code=error_code,
            status_code=400,
        )


class CandidateNotFound(ScoringBaseException):
    def __init__(
        self,
        details: str | None = None,
        error_code: str | None = None,
    ):
        super().__init__(
            message="Candidate not found",
            details=details,
            error_code=error_code,
            status_code=404,
        )


class CandidateScoreNotFound(ScoringBaseException):
    def __init__(
        self,
        details: str | None = None,
        error_code: str | None = None,
    ):
        super().__init__(
            message="Candidate score not found",
            details=details,
            error_code=error_code,
            status_code=404,
        )


class SourcingServiceClientError(ScoringBaseException):
    def __init__(
        self,
        details: str | None = None,
        error_code: str | None = None,
        status_code: int = 500,
    ):
        super().__init__(
            message="Sourcing service request failed",
            details=details,
            error_code=error_code,
            status_code=status_code,
        )

