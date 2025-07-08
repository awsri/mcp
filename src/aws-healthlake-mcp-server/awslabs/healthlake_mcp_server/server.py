# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

#!/usr/bin/env python3

import boto3
import json
import os
import requests
from typing import Any, Dict, List, Optional, Union

from awslabs.healthlake_mcp_server.common import (
    CreateDatastoreInput,
    StartFHIRImportJobInput,
    StartFHIRExportJobInput,
    Tag,
    handle_exceptions,
    mutation_check,
)
from botocore.config import Config
from mcp.server.fastmcp import FastMCP


# Initialize the MCP server
mcp = FastMCP("AWS HealthLake MCP Server")


def get_healthlake_client(region_name: Optional[str] = None):
    """Get a HealthLake client with proper configuration."""
    if not region_name:
        region_name = os.getenv('AWS_REGION', 'us-west-2')
    
    config = Config(
        region_name=region_name,
        retries={'max_attempts': 3, 'mode': 'adaptive'}
    )
    
    return boto3.client('healthlake', config=config)


@mcp.tool()
@handle_exceptions
def create_datastore(
    datastore_type_version: str,
    datastore_name: Optional[str] = None,
    sse_configuration: Optional[Dict[str, Any]] = None,
    preload_data_config: Optional[Dict[str, Any]] = None,
    client_token: Optional[str] = None,
    tags: Optional[List[Dict[str, str]]] = None,
    identity_provider_configuration: Optional[Dict[str, Any]] = None,
    region_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new HealthLake datastore.
    
    Args:
        datastore_type_version: The FHIR version of the datastore (R4)
        datastore_name: Optional user-generated name for the datastore
        sse_configuration: Optional server-side encryption configuration
        preload_data_config: Optional parameter to preload data upon creation
        client_token: Optional user provided token for idempotency
        tags: Optional list of tags to apply to the datastore
        identity_provider_configuration: Optional identity provider configuration
        region_name: AWS region name (defaults to AWS_REGION env var or us-west-2)
    
    Returns:
        Dict containing the datastore creation response
    """
    mutation_check()
    
    client = get_healthlake_client(region_name)
    
    # Build the request parameters
    params = {
        'DatastoreTypeVersion': datastore_type_version
    }
    
    if datastore_name:
        params['DatastoreName'] = datastore_name
    if sse_configuration:
        params['SseConfiguration'] = sse_configuration
    if preload_data_config:
        params['PreloadDataConfig'] = preload_data_config
    if client_token:
        params['ClientToken'] = client_token
    if tags:
        params['Tags'] = [Tag(**tag).model_dump(by_alias=True) for tag in tags]
    if identity_provider_configuration:
        params['IdentityProviderConfiguration'] = identity_provider_configuration
    
    response = client.create_fhir_datastore(**params)
    return response


@mcp.tool()
@handle_exceptions
def delete_datastore(
    datastore_id: str,
    region_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Delete a HealthLake datastore.
    
    Args:
        datastore_id: The AWS-generated ID for the datastore
        region_name: AWS region name (defaults to AWS_REGION env var or us-west-2)
    
    Returns:
        Dict containing the datastore deletion response
    """
    mutation_check()
    
    client = get_healthlake_client(region_name)
    response = client.delete_fhir_datastore(DatastoreId=datastore_id)
    return response


@mcp.tool()
@handle_exceptions
def describe_datastore(
    datastore_id: str,
    region_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Describe a HealthLake datastore.
    
    Args:
        datastore_id: The AWS-generated ID for the datastore
        region_name: AWS region name (defaults to AWS_REGION env var or us-west-2)
    
    Returns:
        Dict containing the datastore description
    """
    client = get_healthlake_client(region_name)
    response = client.describe_fhir_datastore(DatastoreId=datastore_id)
    return response


@mcp.tool()
@handle_exceptions
def list_datastores(
    filter_dict: Optional[Dict[str, Any]] = None,
    next_token: Optional[str] = None,
    max_results: Optional[int] = None,
    region_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    List HealthLake datastores.
    
    Args:
        filter_dict: Optional filter to apply to the datastore list
        next_token: Optional token for pagination
        max_results: Optional maximum number of results to return
        region_name: AWS region name (defaults to AWS_REGION env var or us-west-2)
    
    Returns:
        Dict containing the list of datastores
    """
    client = get_healthlake_client(region_name)
    
    params = {}
    if filter_dict:
        params['Filter'] = filter_dict
    if next_token:
        params['NextToken'] = next_token
    if max_results:
        params['MaxResults'] = max_results
    
    response = client.list_fhir_datastores(**params)
    return response


@mcp.tool()
@handle_exceptions
def start_fhir_import_job(
    input_data_config: Dict[str, Any],
    job_output_data_config: Dict[str, Any],
    datastore_id: str,
    data_access_role_arn: str,
    job_name: Optional[str] = None,
    client_token: Optional[str] = None,
    region_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Start a FHIR import job.
    
    Args:
        input_data_config: The input properties of the FHIR Import job
        job_output_data_config: The output data configuration
        datastore_id: The AWS-generated datastore ID
        data_access_role_arn: The ARN that gives HealthLake access permission
        job_name: Optional name of the FHIR Import job
        client_token: Optional user provided token
        region_name: AWS region name (defaults to AWS_REGION env var or us-west-2)
    
    Returns:
        Dict containing the import job response
    """
    mutation_check()
    
    client = get_healthlake_client(region_name)
    
    params = {
        'InputDataConfig': input_data_config,
        'JobOutputDataConfig': job_output_data_config,
        'DatastoreId': datastore_id,
        'DataAccessRoleArn': data_access_role_arn
    }
    
    if job_name:
        params['JobName'] = job_name
    if client_token:
        params['ClientToken'] = client_token
    
    response = client.start_fhir_import_job(**params)
    return response


@mcp.tool()
@handle_exceptions
def start_fhir_export_job(
    output_data_config: Dict[str, Any],
    datastore_id: str,
    data_access_role_arn: str,
    job_name: Optional[str] = None,
    client_token: Optional[str] = None,
    region_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Start a FHIR export job.
    
    Args:
        output_data_config: The output data configuration
        datastore_id: The AWS generated ID for the datastore
        data_access_role_arn: The ARN that gives HealthLake access permission
        job_name: Optional user generated name for an export job
        client_token: Optional user provided token
        region_name: AWS region name (defaults to AWS_REGION env var or us-west-2)
    
    Returns:
        Dict containing the export job response
    """
    mutation_check()
    
    client = get_healthlake_client(region_name)
    
    params = {
        'OutputDataConfig': output_data_config,
        'DatastoreId': datastore_id,
        'DataAccessRoleArn': data_access_role_arn
    }
    
    if job_name:
        params['JobName'] = job_name
    if client_token:
        params['ClientToken'] = client_token
    
    response = client.start_fhir_export_job(**params)
    return response


@mcp.tool()
@handle_exceptions
def describe_fhir_import_job(
    datastore_id: str,
    job_id: str,
    region_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Describe a FHIR import job.
    
    Args:
        datastore_id: The AWS-generated ID for the datastore
        job_id: The AWS-generated job ID
        region_name: AWS region name (defaults to AWS_REGION env var or us-west-2)
    
    Returns:
        Dict containing the import job description
    """
    client = get_healthlake_client(region_name)
    response = client.describe_fhir_import_job(
        DatastoreId=datastore_id,
        JobId=job_id
    )
    return response


@mcp.tool()
@handle_exceptions
def describe_fhir_export_job(
    datastore_id: str,
    job_id: str,
    region_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Describe a FHIR export job.
    
    Args:
        datastore_id: The AWS-generated ID for the datastore
        job_id: The AWS-generated job ID
        region_name: AWS region name (defaults to AWS_REGION env var or us-west-2)
    
    Returns:
        Dict containing the export job description
    """
    client = get_healthlake_client(region_name)
    response = client.describe_fhir_export_job(
        DatastoreId=datastore_id,
        JobId=job_id
    )
    return response


@mcp.tool()
@handle_exceptions
def list_fhir_import_jobs(
    datastore_id: str,
    next_token: Optional[str] = None,
    max_results: Optional[int] = None,
    job_name: Optional[str] = None,
    job_status: Optional[str] = None,
    submitted_before: Optional[str] = None,
    submitted_after: Optional[str] = None,
    region_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    List FHIR import jobs.
    
    Args:
        datastore_id: The AWS-generated ID for the datastore
        next_token: Optional token for pagination
        max_results: Optional maximum number of results to return
        job_name: Optional job name filter
        job_status: Optional job status filter
        submitted_before: Optional filter for jobs submitted before this date
        submitted_after: Optional filter for jobs submitted after this date
        region_name: AWS region name (defaults to AWS_REGION env var or us-west-2)
    
    Returns:
        Dict containing the list of import jobs
    """
    client = get_healthlake_client(region_name)
    
    params = {'DatastoreId': datastore_id}
    
    if next_token:
        params['NextToken'] = next_token
    if max_results:
        params['MaxResults'] = max_results
    if job_name:
        params['JobName'] = job_name
    if job_status:
        params['JobStatus'] = job_status
    if submitted_before:
        params['SubmittedBefore'] = submitted_before
    if submitted_after:
        params['SubmittedAfter'] = submitted_after
    
    response = client.list_fhir_import_jobs(**params)
    return response


@mcp.tool()
@handle_exceptions
def list_fhir_export_jobs(
    datastore_id: str,
    next_token: Optional[str] = None,
    max_results: Optional[int] = None,
    job_name: Optional[str] = None,
    job_status: Optional[str] = None,
    submitted_before: Optional[str] = None,
    submitted_after: Optional[str] = None,
    region_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    List FHIR export jobs.
    
    Args:
        datastore_id: The AWS-generated ID for the datastore
        next_token: Optional token for pagination
        max_results: Optional maximum number of results to return
        job_name: Optional job name filter
        job_status: Optional job status filter
        submitted_before: Optional filter for jobs submitted before this date
        submitted_after: Optional filter for jobs submitted after this date
        region_name: AWS region name (defaults to AWS_REGION env var or us-west-2)
    
    Returns:
        Dict containing the list of export jobs
    """
    client = get_healthlake_client(region_name)
    
    params = {'DatastoreId': datastore_id}
    
    if next_token:
        params['NextToken'] = next_token
    if max_results:
        params['MaxResults'] = max_results
    if job_name:
        params['JobName'] = job_name
    if job_status:
        params['JobStatus'] = job_status
    if submitted_before:
        params['SubmittedBefore'] = submitted_before
    if submitted_after:
        params['SubmittedAfter'] = submitted_after
    
    response = client.list_fhir_export_jobs(**params)
    return response


@mcp.tool()
@handle_exceptions
def read_fhir_resource(
    datastore_id: str,
    resource_type: str,
    resource_id: str,
    region_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Read a FHIR resource by ID.
    
    Args:
        datastore_id: The AWS-generated ID for the datastore
        resource_type: The FHIR resource type (e.g., Patient, Observation)
        resource_id: The ID of the FHIR resource
        region_name: AWS region name (defaults to AWS_REGION env var or us-west-2)
    
    Returns:
        Dict containing the FHIR resource
    """
    if not region_name:
        region_name = os.getenv('AWS_REGION', 'us-west-2')
    
    # Get the datastore endpoint
    client = get_healthlake_client(region_name)
    datastore_info = client.describe_fhir_datastore(DatastoreId=datastore_id)
    endpoint = datastore_info['DatastoreProperties']['DatastoreEndpoint']
    
    # Construct the URL for the FHIR resource
    url = f"{endpoint}{resource_type}/{resource_id}"
    
    # Get AWS SigV4 signed headers
    session = boto3.Session()
    credentials = session.get_credentials()
    
    # Create a request with AWS SigV4 authentication
    auth = boto3.auth.SigV4Auth(credentials, 'healthlake', region_name)
    request = requests.Request('GET', url)
    prepared_request = request.prepare()
    auth.add_auth(prepared_request)
    
    # Send the request
    with requests.Session() as session:
        response = session.send(prepared_request)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        return response.json()


@mcp.tool()
@handle_exceptions
def search_fhir_resources(
    datastore_id: str,
    resource_type: str,
    query_parameters: Optional[Dict[str, str]] = None,
    region_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Search for FHIR resources.
    
    Args:
        datastore_id: The AWS-generated ID for the datastore
        resource_type: The FHIR resource type to search (e.g., Patient, Observation)
        query_parameters: Optional dictionary of search parameters
        region_name: AWS region name (defaults to AWS_REGION env var or us-west-2)
    
    Returns:
        Dict containing the search results
    """
    if not region_name:
        region_name = os.getenv('AWS_REGION', 'us-west-2')
    
    # Get the datastore endpoint
    client = get_healthlake_client(region_name)
    datastore_info = client.describe_fhir_datastore(DatastoreId=datastore_id)
    endpoint = datastore_info['DatastoreProperties']['DatastoreEndpoint']
    
    # Construct the URL for the FHIR search
    url = f"{endpoint}{resource_type}"
    
    # Get AWS SigV4 signed headers
    session = boto3.Session()
    credentials = session.get_credentials()
    
    # Create a request with AWS SigV4 authentication
    auth = boto3.auth.SigV4Auth(credentials, 'healthlake', region_name)
    request = requests.Request('GET', url, params=query_parameters)
    prepared_request = request.prepare()
    auth.add_auth(prepared_request)
    
    # Send the request
    with requests.Session() as session:
        response = session.send(prepared_request)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        return response.json()


@mcp.tool()
@handle_exceptions
def create_fhir_resource(
    datastore_id: str,
    resource_type: str,
    resource_data: Dict[str, Any],
    region_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new FHIR resource.
    
    Args:
        datastore_id: The AWS-generated ID for the datastore
        resource_type: The FHIR resource type (e.g., Patient, Observation)
        resource_data: The FHIR resource data as a dictionary
        region_name: AWS region name (defaults to AWS_REGION env var or us-west-2)
    
    Returns:
        Dict containing the created FHIR resource
    """
    mutation_check()
    
    if not region_name:
        region_name = os.getenv('AWS_REGION', 'us-west-2')
    
    # Get the datastore endpoint
    client = get_healthlake_client(region_name)
    datastore_info = client.describe_fhir_datastore(DatastoreId=datastore_id)
    endpoint = datastore_info['DatastoreProperties']['DatastoreEndpoint']
    
    # Construct the URL for the FHIR resource
    url = f"{endpoint}{resource_type}"
    
    # Get AWS SigV4 signed headers
    session = boto3.Session()
    credentials = session.get_credentials()
    
    # Create a request with AWS SigV4 authentication
    auth = boto3.auth.SigV4Auth(credentials, 'healthlake', region_name)
    request = requests.Request('POST', url, json=resource_data)
    prepared_request = request.prepare()
    auth.add_auth(prepared_request)
    
    # Send the request
    with requests.Session() as session:
        response = session.send(prepared_request)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        return response.json()


@mcp.tool()
@handle_exceptions
def update_fhir_resource(
    datastore_id: str,
    resource_type: str,
    resource_id: str,
    resource_data: Dict[str, Any],
    region_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update an existing FHIR resource.
    
    Args:
        datastore_id: The AWS-generated ID for the datastore
        resource_type: The FHIR resource type (e.g., Patient, Observation)
        resource_id: The ID of the FHIR resource to update
        resource_data: The updated FHIR resource data as a dictionary
        region_name: AWS region name (defaults to AWS_REGION env var or us-west-2)
    
    Returns:
        Dict containing the updated FHIR resource
    """
    mutation_check()
    
    if not region_name:
        region_name = os.getenv('AWS_REGION', 'us-west-2')
    
    # Get the datastore endpoint
    client = get_healthlake_client(region_name)
    datastore_info = client.describe_fhir_datastore(DatastoreId=datastore_id)
    endpoint = datastore_info['DatastoreProperties']['DatastoreEndpoint']
    
    # Construct the URL for the FHIR resource
    url = f"{endpoint}{resource_type}/{resource_id}"
    
    # Ensure the resource ID in the URL matches the one in the resource data
    if 'id' not in resource_data:
        resource_data['id'] = resource_id
    
    # Get AWS SigV4 signed headers
    session = boto3.Session()
    credentials = session.get_credentials()
    
    # Create a request with AWS SigV4 authentication
    auth = boto3.auth.SigV4Auth(credentials, 'healthlake', region_name)
    request = requests.Request('PUT', url, json=resource_data)
    prepared_request = request.prepare()
    auth.add_auth(prepared_request)
    
    # Send the request
    with requests.Session() as session:
        response = session.send(prepared_request)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        return response.json()


@mcp.tool()
@handle_exceptions
def delete_fhir_resource(
    datastore_id: str,
    resource_type: str,
    resource_id: str,
    region_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Delete a FHIR resource.
    
    Args:
        datastore_id: The AWS-generated ID for the datastore
        resource_type: The FHIR resource type (e.g., Patient, Observation)
        resource_id: The ID of the FHIR resource to delete
        region_name: AWS region name (defaults to AWS_REGION env var or us-west-2)
    
    Returns:
        Dict containing the deletion response
    """
    mutation_check()
    
    if not region_name:
        region_name = os.getenv('AWS_REGION', 'us-west-2')
    
    # Get the datastore endpoint
    client = get_healthlake_client(region_name)
    datastore_info = client.describe_fhir_datastore(DatastoreId=datastore_id)
    endpoint = datastore_info['DatastoreProperties']['DatastoreEndpoint']
    
    # Construct the URL for the FHIR resource
    url = f"{endpoint}{resource_type}/{resource_id}"
    
    # Get AWS SigV4 signed headers
    session = boto3.Session()
    credentials = session.get_credentials()
    
    # Create a request with AWS SigV4 authentication
    auth = boto3.auth.SigV4Auth(credentials, 'healthlake', region_name)
    request = requests.Request('DELETE', url)
    prepared_request = request.prepare()
    auth.add_auth(prepared_request)
    
    # Send the request
    with requests.Session() as session:
        response = session.send(prepared_request)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        # DELETE might not return content
        if response.content:
            return response.json()
        else:
            return {"status": "success", "statusCode": response.status_code}


@mcp.tool()
@handle_exceptions
def tag_resource(
    resource_arn: str,
    tags: List[Dict[str, str]],
    region_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Add tags to a HealthLake resource.
    
    Args:
        resource_arn: The Amazon Resource Name (ARN) of the resource
        tags: List of tags to add to the resource
        region_name: AWS region name (defaults to AWS_REGION env var or us-west-2)
    
    Returns:
        Dict containing the tag resource response
    """
    mutation_check()
    
    client = get_healthlake_client(region_name)
    
    tag_objects = [Tag(**tag).model_dump(by_alias=True) for tag in tags]
    
    response = client.tag_resource(
        ResourceARN=resource_arn,
        Tags=tag_objects
    )
    return response


@mcp.tool()
@handle_exceptions
def untag_resource(
    resource_arn: str,
    tag_keys: List[str],
    region_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Remove tags from a HealthLake resource.
    
    Args:
        resource_arn: The Amazon Resource Name (ARN) of the resource
        tag_keys: List of tag keys to remove from the resource
        region_name: AWS region name (defaults to AWS_REGION env var or us-west-2)
    
    Returns:
        Dict containing the untag resource response
    """
    mutation_check()
    
    client = get_healthlake_client(region_name)
    
    response = client.untag_resource(
        ResourceARN=resource_arn,
        TagKeys=tag_keys
    )
    return response


@mcp.tool()
@handle_exceptions
def list_tags_for_resource(
    resource_arn: str,
    region_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    List tags for a HealthLake resource.
    
    Args:
        resource_arn: The Amazon Resource Name (ARN) of the resource
        region_name: AWS region name (defaults to AWS_REGION env var or us-west-2)
    
    Returns:
        Dict containing the resource tags
    """
    client = get_healthlake_client(region_name)
    
    response = client.list_tags_for_resource(ResourceARN=resource_arn)
    return response


def main():
    """Main entry point for the HealthLake MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
