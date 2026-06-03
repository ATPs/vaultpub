class VaultpubError(Exception):
    """Base exception for vaultpub."""


class ConfigError(VaultpubError):
    """Configuration error."""


class PathTraversalError(VaultpubError):
    """Attempted path traversal outside vault root."""


class NoteNotFoundError(VaultpubError):
    """Requested note not found in vault."""


class AttachmentNotFoundError(VaultpubError):
    """Requested attachment not found."""


class RenderError(VaultpubError):
    """Error during rendering."""


class CircularEmbedError(RenderError):
    """Circular embed detected."""
