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

### Installing in Claude Desktop

```bash
mcp install latentsense_server.py --name "Latentsense Server" -v LATENTSENSE_API_KEY=your-key-here
```

Or with environment file:
```bash
mcp install latentsense_server.py -f .env
```

## Available Tools

### 1. `get_project_runs`
Get all past cog runs in a project with optional filtering and sorting.

**Parameters:**
- `project_id` (required): Unique ID of the Project
- `filter_cog_name` (optional): Filter by cog type (deidentification, relationships, ai_authorship_detection, knowledge_graph)
- `filter_user_id` (optional): Filter by user ID
- `filter_api_key_id` (optional): Filter by API key ID
- `page` (optional): Page number (default: 1)
- `rows_per_page` (optional): Results per page (default: 50)
- `sort_by` (optional): Sort by 'time' or 'cost' (default: 'time')
- `descending` (optional): Sort order (default: true)

### 2. `get_run_results`
Fetch the full results of a past run from its unique ID.

**Parameters:**
- `run_id` (required): The run ID from previous responses

### 3. `redact_pii`
Redact PII (Personal Identifiable Information) from documents.

**Parameters:**
- `project_id` (required): Unique ID of the Project
- `files` (required): Array of file paths to redact (txt, csv, json, html)

### 4. `redact_relevance`
Remove information from documents that is relevant to a given intent text.

**Parameters:**
- `project_id` (required): Unique ID of the Project
- `files` (required): Array of file paths to redact
- `relevance_term_file` (required): Path to txt file with the subject to redact
- `cutoff` (required): Number between 0 and 1 (lower = more redaction)

### 5. `extract_relationships`
List relationship propositions in documents that are salient and relevant to intent text.

**Parameters:**
- `project_id` (required): Unique ID of the Project
- `files` (required): Array of file paths to analyze
- `claim_concepts_file` (required): Path to txt file with subject of interest

### 6. `create_knowledge_graph`
Create a knowledge map where nodes are concepts and edges are relationships.

**Parameters:**
- `project_id` (required): Unique ID of the Project
- `files` (required): Array of file paths to map relationships from
- `files2` (optional): Additional set of files for comparison
- `concepts_file` (optional): Path to txt file with comma-separated concepts
- `files1_name` (optional): Name for first file set (default: "set_1")
- `files2_name` (optional): Name for second file set (default: "set_2")

### 7. `get_rex_message`
Get Rex chat message history for a specific run.

**Parameters:**
- `project_id` (required): Unique ID of the Project
- `run_id` (required): The ReasonerX run ID

### 8. `send_rex_message`
Send a message to Rex (reasoning agent) based on a knowledge graph.

**Parameters:**
- `project_id` (required): Unique ID of the Project
- `message` (required): The message to send to Rex
- `run_id` (required): The ReasonerX run ID
- `graph` (optional): Modified graph object with nodes and edges

## Support

For issues related to:
- **This MCP server**: Open an issue in this repository
- **Latentsense API**: Contact Latentsense support
- **MCP Protocol**: See the [Model Context Protocol documentation](https://modelcontextprotocol.io)