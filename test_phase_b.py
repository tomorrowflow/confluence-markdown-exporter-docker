import os
import subprocess
import tempfile


def test_environment_configuration():
    """Test Phase B - Environment Configuration."""
    print("🧪 Testing Phase B: Environment Configuration")
    print("=" * 50)

    # Create test environment file
    test_env_content = """
CONFLUENCE_URL=https://test.atlassian.net
CONFLUENCE_USERNAME=test@example.com
CONFLUENCE_API_TOKEN=test-token-123
CQL_QUERY=space = MFS
CRON_SCHEDULE=0 2 * * *
EXPORT_PATH=/app/exports
MAX_RESULTS=50
LOG_LEVEL=DEBUG
CONTAINER_NAME=test-exporter
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write(test_env_content)
        test_env_file = f.name

    try:
        tests = [
            ("Build image with env config", "docker build -t confluence-exporter:env-config ."),
            ("Test config validator", "bash docker/config-validator.sh"),
            (
                "Test container with env file",
                f"docker run --rm --env-file {test_env_file} confluence-exporter:env-config echo 'Env test complete'",
            ),
        ]

        passed = 0
        failed = 0

        for test_name, command in tests:
            print(f"\n🔄 Running: {test_name}")

            if "config-validator" in command:
                # Source env file for validator test
                env = os.environ.copy()
                with open(test_env_file, "r") as f:
                    for line in f:
                        if "=" in line and not line.startswith("#"):
                            key, value = line.strip().split("=", 1)
                            env[key] = value

                result = subprocess.run(
                    command, check=False, shell=True, capture_output=True, text=True, env=env
                )
            else:
                result = subprocess.run(
                    command, check=False, shell=True, capture_output=True, text=True
                )

            if result.returncode == 0:
                print(f"✅ {test_name}: PASSED")
                passed += 1
            else:
                print(f"❌ {test_name}: FAILED")
                print(f"   Error: {result.stderr}")
                failed += 1

        print("\n" + "=" * 50)
        print(f"Results: {passed} passed, {failed} failed")

        return failed == 0

    finally:
        os.unlink(test_env_file)


if __name__ == "__main__":
    import sys

    success = test_environment_configuration()
    sys.exit(0 if success else 1)
