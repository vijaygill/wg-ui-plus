"""Compatibility fixes required before django-mcp-server initializes its server."""


def rebuild_fastmcp_settings():
    """Resolve FastMCP's generic lifespan annotation before settings inspection.

    mcp 1.9.4 defines ``Settings.lifespan`` with forward references to types
    declared in the same module.  pydantic-settings now inspects that field
    while constructing the Django MCP server and warns when those references
    have not been resolved yet.
    """

    from mcp.server.fastmcp.server import (
        AbstractAsyncContextManager,
        Callable,
        FastMCP,
        LifespanResultT,
        Settings,
    )

    Settings.model_rebuild(
        _types_namespace={
            "AbstractAsyncContextManager": AbstractAsyncContextManager,
            "Callable": Callable,
            "FastMCP": FastMCP,
            "LifespanResultT": LifespanResultT,
        }
    )
