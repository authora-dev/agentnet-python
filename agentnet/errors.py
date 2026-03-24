"""AgentNet SDK error hierarchy."""


class AgentNetError(Exception):
    """Base error for all AgentNet SDK errors."""

    def __init__(self, message: str, status_code: int = 0, code: str | None = None, details: object = None):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.details = details


class NetworkError(AgentNetError):
    def __init__(self, message: str = "Network error", details: object = None):
        super().__init__(message, 0, "NETWORK_ERROR", details)


class TimeoutError(AgentNetError):
    def __init__(self, message: str = "Request timed out"):
        super().__init__(message, 408, "TIMEOUT")


class AuthenticationError(AgentNetError):
    def __init__(self, message: str = "Authentication failed", details: object = None):
        super().__init__(message, 401, "AUTHENTICATION_ERROR", details)


class AuthorizationError(AgentNetError):
    def __init__(self, message: str = "Forbidden", details: object = None):
        super().__init__(message, 403, "AUTHORIZATION_ERROR", details)


class NotFoundError(AgentNetError):
    def __init__(self, message: str = "Resource not found", details: object = None):
        super().__init__(message, 404, "NOT_FOUND", details)


class RateLimitError(AgentNetError):
    def __init__(self, message: str = "Rate limit exceeded", retry_after: int | None = None, details: object = None):
        super().__init__(message, 429, "RATE_LIMIT", details)
        self.retry_after = retry_after


class InsufficientFundsError(AgentNetError):
    def __init__(self, message: str, balance_cents: int = 0, required_cents: int = 0, details: object = None):
        super().__init__(message, 402, "INSUFFICIENT_FUNDS", details)
        self.balance_cents = balance_cents
        self.required_cents = required_cents


class NoWorkersError(AgentNetError):
    def __init__(self, message: str, region: str | None = None, alternative_regions: list[str] | None = None):
        super().__init__(message, 503, "NO_WORKERS")
        self.region = region
        self.alternative_regions = alternative_regions or []


class TaskError(AgentNetError):
    def __init__(self, message: str, task_id: str, code: str | None = None):
        super().__init__(message, 500, code or "TASK_ERROR")
        self.task_id = task_id
