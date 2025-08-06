# Propylon Document Manager Assessment

The Propylon Document Management Technical Assessment is a simple (and incomplete) web application consisting of a basic API backend and a React based client.  This API/client can be used as a bootstrap to implement the specific features requested in the assessment description. 

## Getting Started
### API Development
The API project is a [Django/DRF](https://www.django-rest-framework.org/) project that utilizes a [Makefile](https://www.gnu.org/software/make/manual/make.html) for a convenient interface to access development utilities. This application uses [SQLite](https://www.sqlite.org/index.html) as the default persistence database you are more than welcome to change this. This project requires Python 3.11 in order to create the virtual environment.  You will need to ensure that this version of Python is installed on your OS before building the virtual environment.  Running the below commmands should get the development environment running using the Django development server.
1. `$ make build` to create the virtual environment.
2. `$ make fixtures` to create a small number of fixture file versions.
3. `$ make serve` to start the development server on port 8001.
4. `$ make test` to run the limited test suite via PyTest.

Got it! Here's a revised version of your README without listing individual API endpoints, leveraging Swagger documentation instead:

---

# Propylon Document Manager

## Overview

The Propylon Document Manager provides authenticated users a secure platform for storing and managing file versions at specified URLs. The system ensures data integrity through version control and provides mechanisms to retrieve files using URL and Content Addressable Storage (CAS) identifiers.

## Key Features

### 1. User Management

- **Custom User Model:** A custom user model extends Django's `AbstractUser`, using email as the unique identifier and primary authentication mechanism.
- **Authentication:** Non-authenticated users are restricted from interacting with the application.

### 2. File Versioning

- **Automatic Versioning:** Uploaded files automatically increment version numbers if stored at the same URL.
- **Content Addressable Storage (CAS):** Files are hash-verified using `md5` to generate unique CAS URLs for identification.

### 3. File Sharing

- **File Sharing Model:** Manages sharing permissions based on specified edit and delete capabilities between users.

Documentation Access
Interactive API documentation is available to facilitate easy testing and integration:

- Swagger UI: Access the API documentation at **/schema/swagger-ui/**.
- ReDoc: Access the elegant API documentation at **/schema/redoc/**.
## Permissions and Security

- **File Access Control:** Implemented through custom permission classes to ensure:
  - Owners manage their own files.
  - Shared file access is regulated based on predefined permissions.

## Validators

- **File Extension Validation:** Ensures uploaded files conform to allowed extensions using the `validate_file_extension` function.

## Project Capabilities

1. **Interactivity:** Restricts application interaction to authenticated users.
2. **File Isolation:** Prevents users from accessing files submitted by others.
3. **Revisions:** Supports storing multiple versions for files at the same URL.
4. **Retrieval:** Enables fetching any file version via both URL and CAS mechanisms.

This documentation provides a concise overview of the core functionality and architecture of the Propylon Document Manager. For detailed API interactions, refer to the Swagger UI provided with the application.

### Client Development 
See the Readme [here](https://github.com/propylon/document-manager-assessment/blob/main/client/doc-manager/README.md)

##
[![Built with Cookiecutter Django](https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg?logo=cookiecutter)](https://github.com/cookiecutter/cookiecutter-django/)
