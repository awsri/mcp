# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-07-08

### Added
- FHIR CRUD API operations:
  - `read_fhir_resource`: Retrieve FHIR resources by ID
  - `search_fhir_resources`: Search for FHIR resources using query parameters
  - `create_fhir_resource`: Create new FHIR resources
  - `update_fhir_resource`: Update existing FHIR resources
  - `delete_fhir_resource`: Delete FHIR resources
- Added requests library dependency
- Updated documentation with FHIR CRUD API examples
- Updated IAM permission recommendations

## [1.0.0] - 2025-07-01

### Added
- Initial release of AWS HealthLake MCP Server
- Support for datastore operations (create, delete, describe, list)
- Support for FHIR import/export job operations
- Support for resource tagging operations
- Read-only mode support via HEALTHLAKE_MCP_READONLY environment variable
- Comprehensive error handling and logging
- Full AWS credential integration
- Support for all AWS regions
