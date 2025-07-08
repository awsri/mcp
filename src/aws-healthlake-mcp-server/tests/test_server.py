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

import os
import pytest
from unittest.mock import MagicMock, patch

from awslabs.healthlake_mcp_server.server import (
    create_datastore,
    delete_datastore,
    describe_datastore,
    list_datastores,
    read_fhir_resource,
    search_fhir_resources,
    create_fhir_resource,
    update_fhir_resource,
    delete_fhir_resource,
)


@pytest.fixture
def mock_boto3_client():
    with patch('boto3.client') as mock_client:
        yield mock_client


@pytest.fixture
def mock_requests_session():
    with patch('requests.Session') as mock_session:
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"resourceType": "Patient", "id": "test-id"}
        mock_response.content = b'{"resourceType": "Patient", "id": "test-id"}'
        mock_response.status_code = 200
        
        mock_session_instance = MagicMock()
        mock_session_instance.send.return_value = mock_response
        mock_session.return_value.__enter__.return_value = mock_session_instance
        
        yield mock_session


@pytest.fixture
def mock_boto3_session():
    with patch('boto3.Session') as mock_session:
        mock_credentials = MagicMock()
        mock_session.return_value.get_credentials.return_value = mock_credentials
        
        mock_auth = MagicMock()
        with patch('boto3.auth.SigV4Auth', return_value=mock_auth):
            yield mock_session


def test_list_datastores(mock_boto3_client):
    mock_client_instance = MagicMock()
    mock_client_instance.list_fhir_datastores.return_value = {
        "DatastorePropertiesList": []
    }
    mock_boto3_client.return_value = mock_client_instance
    
    result = list_datastores()
    
    mock_boto3_client.assert_called_once()
    mock_client_instance.list_fhir_datastores.assert_called_once_with()
    assert result == {"DatastorePropertiesList": []}


def test_read_fhir_resource(mock_boto3_client, mock_boto3_session, mock_requests_session):
    mock_client_instance = MagicMock()
    mock_client_instance.describe_fhir_datastore.return_value = {
        "DatastoreProperties": {
            "DatastoreEndpoint": "https://healthlake.us-west-2.amazonaws.com/datastore/123/r4/"
        }
    }
    mock_boto3_client.return_value = mock_client_instance
    
    result = read_fhir_resource(
        datastore_id="123",
        resource_type="Patient",
        resource_id="456"
    )
    
    mock_boto3_client.assert_called_once()
    mock_client_instance.describe_fhir_datastore.assert_called_once_with(DatastoreId="123")
    assert result == {"resourceType": "Patient", "id": "test-id"}


def test_create_fhir_resource(mock_boto3_client, mock_boto3_session, mock_requests_session):
    mock_client_instance = MagicMock()
    mock_client_instance.describe_fhir_datastore.return_value = {
        "DatastoreProperties": {
            "DatastoreEndpoint": "https://healthlake.us-west-2.amazonaws.com/datastore/123/r4/"
        }
    }
    mock_boto3_client.return_value = mock_client_instance
    
    resource_data = {
        "resourceType": "Patient",
        "name": [{"family": "Doe", "given": ["John"]}]
    }
    
    result = create_fhir_resource(
        datastore_id="123",
        resource_type="Patient",
        resource_data=resource_data
    )
    
    mock_boto3_client.assert_called_once()
    mock_client_instance.describe_fhir_datastore.assert_called_once_with(DatastoreId="123")
    assert result == {"resourceType": "Patient", "id": "test-id"}
