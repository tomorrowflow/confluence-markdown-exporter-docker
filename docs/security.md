# Security Documentation

This document outlines the security measures implemented in the confluence-markdown-exporter to protect sensitive information, particularly API keys.

## API Key Security

### 1. Secure Storage

API keys are stored using the `SecretStr` type from Pydantic, which provides a secure way to handle sensitive information. The configuration file itself is stored with restricted file permissions to prevent unauthorized access.

### 2. Prevention of Exposure in Logs and Error Messages

The application includes a robust redaction system that automatically removes sensitive information from:

- Log messages
- Error messages
- Debug output

The `redact_sensitive_info` function is used throughout the codebase to ensure that any potential exposure of sensitive information is prevented.

### 3. Proper Access Controls for Configuration Files

A dedicated script (`bin/secure_config.sh`) is included to set proper file permissions for the configuration file and its directory. This script is automatically run during setup to ensure that:

- Only the user can read/write the configuration file (`chmod 600`)
- Only the user can access the configuration directory (`chmod 700`)

### 4. Best Practices for API Key Management

To further enhance security, users are encouraged to:

- Regularly rotate API keys
- Use environment variables for sensitive information
- Implement additional access controls at the system level

## Reporting Security Vulnerabilities

If you discover a security vulnerability in the confluence-markdown-exporter, please report it responsibly by:

1. Opening an issue on GitHub
2. Sending an email to the maintainers
3. Using the security contact information in the project's security policy

## Security Resources

- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [NIST API Security Guidelines](https://pages.nist.gov/800-218/)
