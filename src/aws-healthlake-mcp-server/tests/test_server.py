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
from awslabs.healthlake_mcp_server.server import (
    create_datastore,
    create_fhir_bundle,
    create_fhir_resource,
    create_observation_template,
    create_patient_template,
    get_datastore_capabilities,
    get_fhir_resource_history,
    list_datastores,
    read_fhir_resource,
    search_fhir_resources_advanced,
    validate_fhir_resource,
)
from unittest.mock import MagicMock, patch


@pytest.fixture
def mock_boto3_client():
    """Mock boto3 client for testing."""
    with patch('boto3.client') as mock_client:
        yield mock_client


@pytest.fixture
def mock_requests_session():
    """Mock requests session for testing."""
    with patch('requests.Session') as mock_session:
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {'resourceType': 'Patient', 'id': 'test-id'}
        mock_response.content = b'{"resourceType": "Patient", "id": "test-id"}'
        mock_response.status_code = 200

        mock_session_instance = MagicMock()
        mock_session_instance.send.return_value = mock_response
        mock_session.return_value.__enter__.return_value = mock_session_instance

        yield mock_session


@pytest.fixture
def mock_boto3_session():
    """Mock boto3 session for testing."""
    with patch('boto3.Session') as mock_session:
        mock_credentials = MagicMock()
        mock_session_instance = MagicMock()
        mock_session_instance.get_credentials.return_value = mock_credentials
        mock_session.return_value = mock_session_instance
        yield mock_session


class TestHealthLakeServer:
    """Test class for HealthLake MCP server functionality."""

    def test_create_datastore(self, mock_boto3_client):
        """Test creating a datastore."""
        mock_client_instance = MagicMock()
        mock_boto3_client.return_value = mock_client_instance
        mock_client_instance.create_fhir_datastore.return_value = {
            'DatastoreId': 'test-datastore-id',
            'DatastoreArn': 'arn:aws:healthlake:us-west-2:123456789012:datastore/fhir/test-datastore-id',
        }

        result = create_datastore(datastore_type_version='R4', datastore_name='test-datastore')

        assert result['DatastoreId'] == 'test-datastore-id'
        mock_client_instance.create_fhir_datastore.assert_called_once()

    def test_read_fhir_resource(
        self, mock_boto3_client, mock_requests_session, mock_boto3_session
    ):
        """Test reading a FHIR resource."""
        # Mock the describe_fhir_datastore call
        mock_client_instance = MagicMock()
        mock_boto3_client.return_value = mock_client_instance
        mock_client_instance.describe_fhir_datastore.return_value = {
            'DatastoreProperties': {
                'DatastoreEndpoint': 'https://healthlake.us-west-2.amazonaws.com/datastore/test-id/r4/'
            }
        }

        result = read_fhir_resource(
            datastore_id='test-datastore-id',
            resource_type='Patient',
            resource_id='test-patient-id',
        )

        assert result['resourceType'] == 'Patient'
        assert result['id'] == 'test-id'

    def test_validate_fhir_resource_valid_patient(self):
        """Test validating a valid patient FHIR resource."""
        patient_data = {
            'resourceType': 'Patient',
            'name': [{'family': 'Doe', 'given': ['John']}],
            'gender': 'male',
            'birthDate': '1970-01-01',
        }

        result = validate_fhir_resource(patient_data, 'Patient')

        assert result['valid'] is True
        assert len(result['issues']) == 0

    def test_validate_fhir_resource_missing_resource_type(self):
        """Test validating FHIR resource with missing resource type."""
        invalid_data = {'name': [{'family': 'Doe', 'given': ['John']}]}

        result = validate_fhir_resource(invalid_data)

        assert result['valid'] is False
        assert "Missing required 'resourceType' field" in result['issues']

    def test_validate_fhir_resource_type_mismatch(self):
        """Test validating FHIR resource with type mismatch."""
        patient_data = {'resourceType': 'Patient', 'name': [{'family': 'Doe', 'given': ['John']}]}

        result = validate_fhir_resource(patient_data, 'Observation')

        assert result['valid'] is False
        assert 'Resource type mismatch' in result['issues'][0]

    def test_create_patient_template(self):
        """Test creating a patient template."""
        result = create_patient_template(
            family_name='Doe',
            given_names=['John', 'Michael'],
            gender='male',
            birth_date='1970-01-01',
            identifier_system='http://hospital.example.org/mrn',
            identifier_value='MRN123456',
            phone='+1-555-123-4567',
            email='john.doe@example.com',
        )

        assert result['resourceType'] == 'Patient'
        assert result['name'][0]['family'] == 'Doe'
        assert result['name'][0]['given'] == ['John', 'Michael']
        assert result['gender'] == 'male'
        assert result['birthDate'] == '1970-01-01'
        assert len(result['identifier']) == 1
        assert result['identifier'][0]['system'] == 'http://hospital.example.org/mrn'
        assert result['identifier'][0]['value'] == 'MRN123456'
        assert len(result['telecom']) == 2

    def test_create_observation_template(self):
        """Test creating an observation template."""
        result = create_observation_template(
            patient_reference='Patient/test-patient-id',
            code_system='http://loinc.org',
            code_value='8867-4',
            code_display='Heart rate',
            status='final',
            value_quantity={
                'value': 72,
                'unit': 'beats/min',
                'system': 'http://unitsofmeasure.org',
                'code': '/min',
            },
            category_code='vital-signs',
        )

        assert result['resourceType'] == 'Observation'
        assert result['status'] == 'final'
        assert result['code']['coding'][0]['system'] == 'http://loinc.org'
        assert result['code']['coding'][0]['code'] == '8867-4'
        assert result['code']['coding'][0]['display'] == 'Heart rate'
        assert result['subject']['reference'] == 'Patient/test-patient-id'
        assert result['valueQuantity']['value'] == 72
        assert result['category'][0]['coding'][0]['code'] == 'vital-signs'

    def test_search_fhir_resources_advanced(
        self, mock_boto3_client, mock_requests_session, mock_boto3_session
    ):
        """Test advanced FHIR resource search."""
        # Mock the describe_fhir_datastore call
        mock_client_instance = MagicMock()
        mock_boto3_client.return_value = mock_client_instance
        mock_client_instance.describe_fhir_datastore.return_value = {
            'DatastoreProperties': {
                'DatastoreEndpoint': 'https://healthlake.us-west-2.amazonaws.com/datastore/test-id/r4/'
            }
        }

        result = search_fhir_resources_advanced(
            datastore_id='test-datastore-id',
            resource_type='Patient',
            search_parameters={'name': 'Smith'},
            include_parameters=['Patient:general-practitioner'],
            sort_parameters=['family', 'given'],
            count=10,
        )

        assert result['resourceType'] == 'Patient'
        assert result['id'] == 'test-id'

    @patch.dict(os.environ, {'HEALTHLAKE_MCP_READONLY': 'false'})
    def test_create_fhir_bundle(
        self, mock_boto3_client, mock_requests_session, mock_boto3_session
    ):
        """Test creating a FHIR bundle."""
        # Mock the describe_fhir_datastore call
        mock_client_instance = MagicMock()
        mock_boto3_client.return_value = mock_client_instance
        mock_client_instance.describe_fhir_datastore.return_value = {
            'DatastoreProperties': {
                'DatastoreEndpoint': 'https://healthlake.us-west-2.amazonaws.com/datastore/test-id/r4/'
            }
        }

        bundle_resources = [
            {
                'resourceType': 'Patient',
                'name': [{'family': 'Smith', 'given': ['Jane']}],
                'gender': 'female',
                'birthDate': '1985-03-15',
            }
        ]

        result = create_fhir_bundle(
            datastore_id='test-datastore-id',
            bundle_resources=bundle_resources,
            bundle_type='transaction',
        )

        assert result['resourceType'] == 'Patient'
        assert result['id'] == 'test-id'

    def test_get_fhir_resource_history(
        self, mock_boto3_client, mock_requests_session, mock_boto3_session
    ):
        """Test getting FHIR resource history."""
        # Mock the describe_fhir_datastore call
        mock_client_instance = MagicMock()
        mock_boto3_client.return_value = mock_client_instance
        mock_client_instance.describe_fhir_datastore.return_value = {
            'DatastoreProperties': {
                'DatastoreEndpoint': 'https://healthlake.us-west-2.amazonaws.com/datastore/test-id/r4/'
            }
        }

        result = get_fhir_resource_history(
            datastore_id='test-datastore-id',
            resource_type='Patient',
            resource_id='test-patient-id',
        )

        assert result['resourceType'] == 'Patient'
        assert result['id'] == 'test-id'

    def test_get_datastore_capabilities(
        self, mock_boto3_client, mock_requests_session, mock_boto3_session
    ):
        """Test getting datastore capabilities."""
        # Mock the describe_fhir_datastore call
        mock_client_instance = MagicMock()
        mock_boto3_client.return_value = mock_client_instance
        mock_client_instance.describe_fhir_datastore.return_value = {
            'DatastoreProperties': {
                'DatastoreEndpoint': 'https://healthlake.us-west-2.amazonaws.com/datastore/test-id/r4/'
            }
        }

        result = get_datastore_capabilities(datastore_id='test-datastore-id')

        assert result['resourceType'] == 'Patient'
        assert result['id'] == 'test-id'


def test_list_datastores(mock_boto3_client):
    """Test listing datastores."""
    mock_client_instance = MagicMock()
    mock_client_instance.list_fhir_datastores.return_value = {'DatastorePropertiesList': []}
    mock_boto3_client.return_value = mock_client_instance

    result = list_datastores()

    mock_boto3_client.assert_called_once()
    mock_client_instance.list_fhir_datastores.assert_called_once_with()
    assert result == {'DatastorePropertiesList': []}


def test_read_fhir_resource(mock_boto3_client, mock_boto3_session, mock_requests_session):
    """Test reading a FHIR resource."""
    mock_client_instance = MagicMock()
    mock_client_instance.describe_fhir_datastore.return_value = {
        'DatastoreProperties': {
            'DatastoreEndpoint': 'https://healthlake.us-west-2.amazonaws.com/datastore/123/r4/'
        }
    }
    mock_boto3_client.return_value = mock_client_instance

    result = read_fhir_resource(datastore_id='123', resource_type='Patient', resource_id='456')

    mock_boto3_client.assert_called_once()
    mock_client_instance.describe_fhir_datastore.assert_called_once_with(DatastoreId='123')
    assert result == {'resourceType': 'Patient', 'id': 'test-id'}


def test_create_fhir_resource(mock_boto3_client, mock_boto3_session, mock_requests_session):
    """Test creating a FHIR resource."""
    mock_client_instance = MagicMock()
    mock_client_instance.describe_fhir_datastore.return_value = {
        'DatastoreProperties': {
            'DatastoreEndpoint': 'https://healthlake.us-west-2.amazonaws.com/datastore/123/r4/'
        }
    }
    mock_boto3_client.return_value = mock_client_instance

    resource_data = {'resourceType': 'Patient', 'name': [{'family': 'Doe', 'given': ['John']}]}

    result = create_fhir_resource(
        datastore_id='123', resource_type='Patient', resource_data=resource_data
    )

    mock_boto3_client.assert_called_once()
    mock_client_instance.describe_fhir_datastore.assert_called_once_with(DatastoreId='123')
    assert result == {'resourceType': 'Patient', 'id': 'test-id'}
