#!/usr/bin/env python3
"""
E2E Test Runner for OpenVibe Backend

This script runs the complete end-to-end test suite with MOCK_MODE enabled.
It sets up the proper environment, runs all tests, and provides detailed reporting.

Usage:
    python run_e2e_tests.py [options]

Options:
    --verbose, -v       Enable verbose output
    --coverage, -c      Run with coverage reporting
    --specific, -s      Run specific test file (e.g., test_e2e_basic.py)
    --help, -h          Show this help message
"""

import os
import sys
import subprocess
import argparse
import tempfile
import shutil
from pathlib import Path


def setup_environment():
    """Set up the test environment"""
    print("🔧 Setting up test environment...")

    # Ensure we're in the backend directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)

    # Set MOCK_MODE environment variable
    os.environ["MOCK_MODE"] = "true"

    # Create temporary data directory for tests
    temp_dir = tempfile.mkdtemp(prefix="openvibe_test_")
    os.environ["DATA_DIR"] = temp_dir

    print(f"✅ Test environment ready")
    print(f"   - MOCK_MODE: {os.environ.get('MOCK_MODE')}")
    print(f"   - DATA_DIR: {temp_dir}")

    return temp_dir


def cleanup_environment(temp_dir):
    """Clean up the test environment"""
    print("🧹 Cleaning up test environment...")

    # Remove temporary data directory
    if temp_dir and Path(temp_dir).exists():
        shutil.rmtree(temp_dir, ignore_errors=True)
        print(f"   - Removed temp directory: {temp_dir}")

    # Clean up environment variables
    if "MOCK_MODE" in os.environ:
        del os.environ["MOCK_MODE"]
    if "DATA_DIR" in os.environ:
        del os.environ["DATA_DIR"]

    print("✅ Cleanup complete")


def run_tests(verbose=False, coverage=False, specific_test=None):
    """Run the test suite"""
    print("🧪 Running E2E tests...")

    # Build pytest command
    cmd = ["python", "-m", "pytest"]

    # Add test directory
    if specific_test:
        if not specific_test.startswith("tests/"):
            specific_test = f"tests/{specific_test}"
        cmd.append(specific_test)
    else:
        cmd.append("tests/")

    # Add options
    if verbose:
        cmd.extend(["-v", "-s"])
    else:
        cmd.append("-v")

    # Add coverage if requested
    if coverage:
        cmd.extend(
            ["--cov=.", "--cov-report=html:htmlcov", "--cov-report=term-missing"]
        )

    # Add test markers and options
    cmd.extend(["--tb=short", "--strict-markers", "-W", "ignore::DeprecationWarning"])

    print(f"   Command: {' '.join(cmd)}")
    print()

    # Run tests
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode == 0
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
        return False
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False


def check_dependencies():
    """Check that required dependencies are installed"""
    print("🔍 Checking dependencies...")

    required_packages = ["pytest", "flask", "requests"]
    missing_packages = []

    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print("   Please install them with: uv pip install .[dev]")
        return False

    print("✅ All dependencies available")
    return True


def print_summary(success, coverage=False):
    """Print test run summary"""
    print("\n" + "=" * 60)
    print("📊 E2E TEST SUMMARY")
    print("=" * 60)

    if success:
        print("✅ All tests passed!")
        print("\n🎉 Your OpenVibe backend is working correctly in MOCK_MODE")
        print("   - All API endpoints are functional")
        print("   - API key validation works with mock responses")
        print("   - Data storage and retrieval is working")
        print("   - User isolation is properly implemented")
    else:
        print("❌ Some tests failed!")
        print("\n🔍 Check the test output above for details")
        print("   - Look for assertion errors or exceptions")
        print("   - Verify that MOCK_MODE is properly configured")
        print("   - Check that all required dependencies are installed")

    if coverage:
        print(f"\n📈 Coverage report generated in htmlcov/index.html")

    print("\n💡 Tips:")
    print("   - Run with --verbose for more detailed output")
    print("   - Run with --coverage to see code coverage")
    print("   - Run with --specific <test_file> to run individual test files")
    print("   - Check logs for any warnings or errors")

    print("=" * 60)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Run OpenVibe Backend E2E Tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    parser.add_argument(
        "--coverage", "-c", action="store_true", help="Run with coverage reporting"
    )

    parser.add_argument(
        "--specific",
        "-s",
        type=str,
        help="Run specific test file (e.g., test_e2e_basic.py)",
    )

    args = parser.parse_args()

    print("🚀 OpenVibe Backend E2E Test Runner")
    print("=" * 50)

    # Check dependencies first
    if not check_dependencies():
        sys.exit(1)

    # Set up environment
    temp_dir = None
    try:
        temp_dir = setup_environment()

        # Run tests
        success = run_tests(
            verbose=args.verbose, coverage=args.coverage, specific_test=args.specific
        )

        # Print summary
        print_summary(success, coverage=args.coverage)

        # Exit with appropriate code
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n⚠️ Test run interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
    finally:
        if temp_dir:
            cleanup_environment(temp_dir)


if __name__ == "__main__":
    main()
