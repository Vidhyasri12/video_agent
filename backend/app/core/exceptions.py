"""
Custom Exception Taxonomy for VMS & Camera Integrations.
Maps specific domain failures to standard error codes and HTTP responses.
"""

class VmsException(Exception):
    """Base exception for all VMS and Camera operations."""
    def __init__(self, message: str, error_code: str = "VMS_ERROR", status_code: int = 500, doc_ref: str = "https://www.tp-link.com/us/vigi/"):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.doc_ref = doc_ref

    def to_dict(self):
        return {
            "status": "error",
            "error_code": self.error_code,
            "message": self.message,
            "documentation_ref": self.doc_ref
        }

class CameraOfflineError(VmsException):
    """Raised when a camera or VMS server host is unreachable."""
    def __init__(self, message: str = "Camera or VMS server is offline or unreachable."):
        super().__init__(
            message=message,
            error_code="CAMERA_OFFLINE",
            status_code=503,
            doc_ref="https://www.tp-link.com/us/support/faq/vigi-camera-offline/"
        )

class AuthenticationFailedError(VmsException):
    """Raised when RTSP or API authentication credentials fail."""
    def __init__(self, message: str = "Authentication failed for camera or VMS server."):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_FAILED",
            status_code=401,
            doc_ref="https://www.tp-link.com/us/support/faq/vigi-password-setting/"
        )

class RTSPTimeoutError(VmsException):
    """Raised when RTSP video stream handshake times out."""
    def __init__(self, message: str = "RTSP video stream connection timed out."):
        super().__init__(
            message=message,
            error_code="RTSP_TIMEOUT",
            status_code=504,
            doc_ref="https://www.tp-link.com/us/support/faq/vigi-rtsp-stream-guide/"
        )

class UnsupportedCapabilityError(VmsException):
    """Raised when a requested feature or API is not supported by the device or is disabled by feature flag."""
    def __init__(self, message: str = "Requested capability is unsupported or not officially documented by TP-Link."):
        super().__init__(
            message=message,
            error_code="UNSUPPORTED_CAPABILITY",
            status_code=501,
            doc_ref="https://www.tp-link.com/us/vigi/"
        )

class NetworkFailureError(VmsException):
    """Raised when network transport or socket level failure occurs."""
    def __init__(self, message: str = "Network connection failure during camera communication."):
        super().__init__(
            message=message,
            error_code="NETWORK_FAILURE",
            status_code=502,
            doc_ref="https://www.tp-link.com/us/support/faq/vigi-network-troubleshooting/"
        )

class FeatureNotAvailableError(VmsException):
    """Raised when an experimental feature is toggled off in production."""
    def __init__(self, message: str = "This experimental feature is disabled in production build."):
        super().__init__(
            message=message,
            error_code="FEATURE_DISABLED",
            status_code=403,
            doc_ref="https://www.tp-link.com/us/vigi/"
        )
