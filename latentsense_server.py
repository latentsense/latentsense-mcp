import json
import os
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
from collections.abc import AsyncIterator

import aiofiles
import httpx
from mcp.server.fastmcp import FastMCP, Context


@dataclass
class LatentsenseConfig:
    api_key: str
    project_id: str
    base_url: str = "https://controller.latentsense.com"


class LatentsenseClient:
    def __init__(self, config: LatentsenseConfig):
        self.config = config
        self.client = httpx.AsyncClient(
            headers={"x-api-key": self.config.api_key}, timeout=30.0
        )

    async def _make_request(
        self, endpoint: str, method: str = "GET", **kwargs
    ) -> Dict[str, Any]:
        """Make an HTTP request to the Latentsense API."""
        url = f"{self.config.base_url}{endpoint}"

        try:
            response = await self.client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise Exception(f"API request failed: {str(e)}")

    async def get_project_runs(
        self,
        filter_cog_name: Optional[str] = None,
        filter_user_id: Optional[str] = None,
        filter_api_key_id: Optional[str] = None,
        page: int = 1,
        rows_per_page: int = 50,
        sort_by: str = "time",
        descending: bool = True,
    ) -> Dict[str, Any]:
        """Get all past cog runs in a project with optional filtering and sorting."""
        params = {}
        if filter_cog_name:
            params["filterCogName"] = filter_cog_name
        if filter_user_id:
            params["filterUserId"] = filter_user_id
        if filter_api_key_id:
            params["filterApiKeyId"] = filter_api_key_id
        if page:
            params["page"] = page
        if rows_per_page:
            params["rowsPerPage"] = rows_per_page
        if sort_by:
            params["sortBy"] = sort_by
        if descending is not None:
            params["descending"] = descending

        endpoint = f"/api/runs/project/{self.config.project_id}"
        return await self._make_request(endpoint, params=params)

    async def get_run_results(self, run_id: str) -> Dict[str, Any]:
        """Fetch the full results of a past run from its unique ID."""
        endpoint = f"/api/runs/{run_id}/results"
        return await self._make_request(endpoint)

    async def _upload_files(
        self,
        endpoint: str,
        files: List[str],
        additional_files: Optional[Dict[str, str]] = None,
        form_data: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Helper method to upload files with form data."""
        # Validate files exist
        for file_path in files:
            if not Path(file_path).exists():
                raise FileNotFoundError(f"File not found: {file_path}")

        if additional_files:
            for file_path in additional_files.values():
                if file_path and not Path(file_path).exists():
                    raise FileNotFoundError(f"File not found: {file_path}")

        # Prepare multipart form data
        files_data = []

        # Add main files
        for file_path in files:
            async with aiofiles.open(file_path, "rb") as f:
                content = await f.read()
                files_data.append(("files", (Path(file_path).name, content)))

        # Add additional files
        if additional_files:
            for field_name, file_path in additional_files.items():
                if file_path:
                    async with aiofiles.open(file_path, "rb") as f:
                        content = await f.read()
                        files_data.append((field_name, (Path(file_path).name, content)))

        # Add form data
        data = form_data or {}

        return await self._make_request(
            endpoint, method="POST", files=files_data, data=data
        )

    async def redact_pii(self, files: List[str]) -> Dict[str, Any]:
        """Redact PII (Personal Identifiable Information) from documents."""
        endpoint = f"/{self.config.project_id}/redact-pii"
        return await self._upload_files(endpoint, files)

    async def redact_relevance(
        self, files: List[str], relevance_term_file: str, cutoff: float
    ) -> Dict[str, Any]:
        """Remove information from documents that is relevant to a given intent text."""
        endpoint = f"/{self.config.project_id}/redact-relevance"
        additional_files = {"relevance_term": relevance_term_file}
        form_data = {"cutoff": str(cutoff)}

        return await self._upload_files(
            endpoint, files, additional_files=additional_files, form_data=form_data
        )

    async def extract_relationships(
        self, files: List[str], claim_concepts_file: str
    ) -> Dict[str, Any]:
        """List relationship propositions in documents that are salient and relevant to intent text."""
        endpoint = f"/{self.config.project_id}/relationships-from-premises"
        additional_files = {"claim_concepts": claim_concepts_file}

        return await self._upload_files(
            endpoint, files, additional_files=additional_files
        )

    async def create_knowledge_graph(
        self,
        files: List[str],
        files2: Optional[List[str]] = None,
        concepts_file: Optional[str] = None,
        files1_name: Optional[str] = None,
        files2_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a knowledge map where nodes are concepts and edges are relationships."""
        endpoint = f"/{self.config.project_id}/reasoner-x"

        # Prepare files data
        files_data = []

        # Add main files
        for file_path in files:
            if not Path(file_path).exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            async with aiofiles.open(file_path, "rb") as f:
                content = await f.read()
                files_data.append(("files", (Path(file_path).name, content)))

        # Add second set of files if provided
        if files2:
            for file_path in files2:
                if not Path(file_path).exists():
                    raise FileNotFoundError(f"File not found: {file_path}")
                async with aiofiles.open(file_path, "rb") as f:
                    content = await f.read()
                    files_data.append(("files2", (Path(file_path).name, content)))

        # Add concepts file if provided
        if concepts_file and Path(concepts_file).exists():
            async with aiofiles.open(concepts_file, "rb") as f:
                content = await f.read()
                files_data.append(("concepts", (Path(concepts_file).name, content)))

        # Prepare form data
        data = {}
        if files1_name:
            data["files1_name"] = files1_name
        if files2_name:
            data["files2_name"] = files2_name

        return await self._make_request(
            endpoint, method="POST", files=files_data, data=data
        )

    async def get_rex_message(self, run_id: str) -> Dict[str, Any]:
        """Get Rex chat message history for a specific run."""
        endpoint = f"/api/chat/{self.config.project_id}/message_rex"
        params = {"run_id": run_id}
        return await self._make_request(endpoint, params=params)

    async def send_rex_message(
        self, message: str, run_id: str, graph: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send a message to Rex (reasoning agent) based on a knowledge graph."""
        endpoint = f"/api/chat/{self.config.project_id}/message_rex"
        params = {"message": message, "run_id": run_id}

        if graph:
            return await self._make_request(
                endpoint, method="POST", params=params, json=graph
            )
        else:
            return await self._make_request(endpoint, method="POST", params=params)

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


@dataclass
class AppContext:
    latentsense_client: LatentsenseClient


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle with Latentsense client."""
    # Get configuration from environment
    api_key = os.getenv("LATENTSENSE_API_KEY")
    if not api_key:
        raise ValueError("LATENTSENSE_API_KEY environment variable is required")

    project_id = os.getenv("LATENTSENSE_PROJECT_ID")
    if not project_id:
        raise ValueError("LATENTSENSE_PROJECT_ID environment variable required")

    base_url = os.getenv("LATENTSENSE_BASE_URL", "https://controller.latentsense.com")

    config = LatentsenseConfig(
        api_key=api_key, project_id=project_id, base_url=base_url
    )
    client = LatentsenseClient(config)

    try:
        yield AppContext(latentsense_client=client)
    finally:
        await client.close()


# Create the FastMCP server
mcp = FastMCP("latentsense-server", lifespan=app_lifespan)


@mcp.tool()
async def get_project_runs(
    ctx: Context,
    filter_cog_name: Optional[str] = None,
    filter_user_id: Optional[str] = None,
    filter_api_key_id: Optional[str] = None,
    page: int = 1,
    rows_per_page: int = 50,
    sort_by: str = "time",
    descending: bool = True,
) -> str:
    """Get all past cog runs in a project with optional filtering and sorting.

    Args:
        filter_cog_name: Only show results from the selected Cog (deidentification, relationships, ai_authorship_detection, knowledge_graph)
        filter_user_id: Only return runs created by the user with the given ID
        filter_api_key_id: Only return runs created by the given API key
        page: The page number of results to return
        rows_per_page: The number of runs to return per page
        sort_by: How to sort the runs (time, cost)
        descending: Whether to sort results in descending order
    """
    client = ctx.request_context.lifespan_context.latentsense_client

    # Validate filter_cog_name if provided
    valid_cog_names = [
        "deidentification",
        "relationships",
        "ai_authorship_detection",
        "knowledge_graph",
    ]
    if filter_cog_name and filter_cog_name not in valid_cog_names:
        return f"Error: filter_cog_name must be one of {valid_cog_names}"

    # Validate sort_by
    valid_sort_by = ["time", "cost"]
    if sort_by not in valid_sort_by:
        return f"Error: sort_by must be one of {valid_sort_by}"

    try:
        result = await client.get_project_runs(
            filter_cog_name=filter_cog_name,
            filter_user_id=filter_user_id,
            filter_api_key_id=filter_api_key_id,
            page=page,
            rows_per_page=rows_per_page,
            sort_by=sort_by,
            descending=descending,
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def get_run_results(ctx: Context, run_id: str) -> str:
    """Fetch the full results of a past run from its unique ID.

    Args:
        run_id: The run ID, returned in previous run responses
    """
    client = ctx.request_context.lifespan_context.latentsense_client

    try:
        result = await client.get_run_results(run_id)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def redact_pii(ctx: Context, files: List[str]) -> str:
    """Redact PII (Personal Identifiable Information) from documents.

    Args:
        files: Array of file paths to redact (txt, csv, json, html)
    """
    client = ctx.request_context.lifespan_context.latentsense_client

    try:
        result = await client.redact_pii(files)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def redact_relevance(
    ctx: Context,
    files: List[str],
    relevance_term_file: str,
    cutoff: float,
) -> str:
    """Remove information from documents that is relevant to a given intent text.

    Args:
        files: Array of file paths to redact (txt, csv, json, html)
        relevance_term_file: Path to txt file with the subject to redact from the main text
        cutoff: Number between 0 and 1. Lower numbers result in more redaction
    """
    client = ctx.request_context.lifespan_context.latentsense_client

    # Validate cutoff
    if not 0 <= cutoff <= 1:
        return "Error: cutoff must be a number between 0 and 1"

    try:
        result = await client.redact_relevance(files, relevance_term_file, cutoff)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def extract_relationships(
    ctx: Context,
    files: List[str],
    claim_concepts_file: str,
) -> str:
    """List relationship propositions in documents that are salient and relevant to intent text.

    Args:
        files: Array of file paths to analyze (txt, csv, json, html)
        claim_concepts_file: Path to txt file with a subject of interest
    """
    client = ctx.request_context.lifespan_context.latentsense_client

    try:
        result = await client.extract_relationships(files, claim_concepts_file)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def create_knowledge_graph(
    ctx: Context,
    files: List[str],
    files2: Optional[List[str]] = None,
    concepts_file: Optional[str] = None,
    files1_name: str = "set_1",
    files2_name: str = "set_2",
) -> str:
    """Create a knowledge map where nodes are concepts and edges are relationships.

    Args:
        files: Array of file paths to map relationships from (txt, csv, json, html)
        files2: Additional set of files for comparison
        concepts_file: Path to txt file containing comma separated concepts expected to be nodes
        files1_name: Name for the first set of files
        files2_name: Name for the second set of files
    """
    client = ctx.request_context.lifespan_context.latentsense_client

    try:
        result = await client.create_knowledge_graph(
            files=files,
            files2=files2,
            concepts_file=concepts_file,
            files1_name=files1_name,
            files2_name=files2_name,
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def get_rex_message(ctx: Context, run_id: str) -> str:
    """Get Rex chat message history for a specific run.

    Args:
        run_id: The ReasonerX run ID to get messages for
    """
    client = ctx.request_context.lifespan_context.latentsense_client

    try:
        result = await client.get_rex_message(run_id)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def send_rex_message(
    ctx: Context,
    message: str,
    run_id: str,
    graph: Optional[Dict[str, Any]] = None,
) -> str:
    """Send a message to Rex (reasoning agent) based on a knowledge graph.

    Args:
        message: The message to send to Rex
        run_id: The ReasonerX run ID to reason under
        graph: Optional modified graph for the next message with nodes and edges
    """
    client = ctx.request_context.lifespan_context.latentsense_client

    try:
        result = await client.send_rex_message(message, run_id, graph)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"


if __name__ == "__main__":
    mcp.run()
