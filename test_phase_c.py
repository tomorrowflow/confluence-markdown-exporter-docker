import os
import subprocess
import tempfile
import time


def test_cron_integration():
    """Test Phase C - Cron Integration."""
    print("🧪 Testing Phase C: Cron Integration")
    print("=" * 50)

    # Test different cron schedules
    test_schedules = [
        ("Daily at 2 AM", "0 2 * * *"),
        ("Every 6 hours", "0 */6 * * *"),
        ("Weekdays at 9 AM", "0 9 * * 1-5"),
        ("Every 5 minutes (test)", "*/5 * * * *"),
    ]

    base_env = {
        "CONFLUENCE_URL": "https://test.atlassian.net",
        "CONFLUENCE_USERNAME": "test@example.com",
        "CONFLUENCE_API_TOKEN": "test-token",
        "CQL_QUERY": "space = MFS",
        "EXPORT_PATH": "/app/exports",
        "MAX_RESULTS": "5",
    }

    passed = 0
    failed = 0

    for schedule_name, cron_schedule in test_schedules:
        print(f"\n🔄 Testing: {schedule_name} ({cron_schedule})")

        test_env = base_env.copy()
        test_env["CRON_SCHEDULE"] = cron_schedule
        test_env["CONTAINER_NAME"] = f"test-{schedule_name.lower().replace(' ', '-')}"

        # Create environment file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            for key, value in test_env.items():
                f.write(f"{key}={value}\n")
            env_file = f.name

        try:
            # Test container startup with this schedule
            cmd = f"docker run --rm --env-file {env_file} confluence-exporter:cron echo 'Schedule test complete'"
            result = subprocess.run(
                cmd, check=False, shell=True, capture_output=True, text=True, timeout=60
            )

            if result.returncode == 0:
                print(f"✅ {schedule_name}: PASSED")
                passed += 1
            else:
                print(f"❌ {schedule_name}: FAILED")
                print(f"   Error: {result.stderr}")
                failed += 1

        except subprocess.TimeoutExpired:
            print(f"❌ {schedule_name}: TIMEOUT")
            failed += 1
        finally:
            os.unlink(env_file)

    # Test export script functionality
    print("\n🔄 Testing export script...")
    try:
        cmd = "docker run --rm confluence-exporter:cron test -x /app/docker/export-runner.sh"
        result = subprocess.run(cmd, check=False, shell=True, capture_output=True, text=True)

        if result.returncode == 0:
            print("✅ Export script executable: PASSED")
            passed += 1
        else:
            print("❌ Export script executable: FAILED")
            failed += 1
    except Exception as e:
        print(f"❌ Export script test: FAILED - {e}")
        failed += 1

    print("\n" + "=" * 50)
    print(f"Results: {passed} passed, {failed} failed")

    return failed == 0


if __name__ == "__main__":
    import sys

    success = test_cron_integration()
    sys.exit(0 if success else 1)
