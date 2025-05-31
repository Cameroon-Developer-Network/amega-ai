# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project setup
- Backend security implementation with role-based access control (RBAC)
- Role hierarchy system with admin, moderator, and user roles
- Security test suite for RBAC functionality
- DeepSource integration for code quality

### Changed
- Updated DeepSource configuration for Python and Shell analysis
- Simplified .deepsource.toml configuration
- Fixed role hierarchy implementation in security middleware

### Deprecated
- N/A

### Removed
- N/A

### Fixed
- N/A

### Security
- Implemented role-based access control (RBAC) middleware
- Added security headers middleware
- Created role hierarchy with proper permission inheritance 