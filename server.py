from morpheus_mcp_server import *  # noqa: F401,F403


def main() -> None:
    """Run the Morpheus MCP server over stdio.

    This repository supports stdio transport for local MCP clients and the
    benchmark harness. See the repo-root `.mcp.json` for the machine-readable
    startup contract.
    """
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
