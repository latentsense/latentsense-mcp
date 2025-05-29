# Latentsense MCP Server

A Python MCP (Model Context Protocol) server for interacting with the Latentsense API. This server provides tools for document processing, relationship extraction, knowledge graph creation, and AI-powered chat interactions.

## Features

- **Document Processing**: Redact PII and relevance-based information from documents
- **Relationship Extraction**: Extract relationships from documents based on concept claims
- **Knowledge Graph Creation**: Generate knowledge graphs from document sets
- **Rex Chat Integration**: Interact with Rex, Latentsense's reasoning agent
- **Run Management**: List and retrieve results from past processing runs

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Set the required environment variables:

```bash
export LATENTSENSE_API_KEY="your-api-key-here"
export LATENTSENSE_PROJECT_ID="your-project-id"
export LATENTSENSE_BASE_URL="https://controller.latentsense.com"  # Optional, defaults to this URL
```

## Usage

### Running the Server

#### With Python directly
```bash
python latentsense_server.py
```

#### With MCP CLI
```bash
mcp run latentsense_server.py
```

#### For development/testing
```bash
mcp dev latentsense_server.py
```




## Support

For issues related to:
- **This MCP server**: Open an issue in this repository
- **Latentsense API**: Contact Latentsense support
- **MCP Protocol**: See the [Model Context Protocol documentation](https://modelcontextprotocol.io)