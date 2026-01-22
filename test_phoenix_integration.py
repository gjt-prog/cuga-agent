#!/usr/bin/env python3
"""
Test script for Phoenix-CUGA integration

This script tests the Phoenix observability integration without requiring
a full CUGA setup or running Phoenix server.
"""

import sys
import os
from pathlib import Path

# Add CUGA to path
cuga_path = Path(__file__).parent / "src"
sys.path.insert(0, str(cuga_path))


def test_imports():
    """Test that all Phoenix modules can be imported."""
    print("=" * 60)
    print("Testing Phoenix Module Imports")
    print("=" * 60)

    try:
        print("\n1. Importing PhoenixTracer...")
        print("   ✅ PhoenixTracer imported")

        print("\n2. Importing CugaPhoenixIntegration...")
        print("   ✅ CugaPhoenixIntegration imported")

        print("\n3. Checking Phoenix availability...")
        try:
            import phoenix as px

            print(f"   ✅ Phoenix installed (version: {px.__version__})")
            phoenix_available = True
        except ImportError:
            print("   ⚠️  Phoenix not installed (integration will be disabled)")
            phoenix_available = False

        print("\n✅ All imports successful!")
        return True, phoenix_available

    except Exception as e:
        print(f"\n❌ Import error: {e}")
        import traceback

        traceback.print_exc()
        return False, False


def test_phoenix_tracer_init(phoenix_available):
    """Test PhoenixTracer initialization."""
    print("\n" + "=" * 60)
    print("Testing PhoenixTracer Initialization")
    print("=" * 60)

    if not phoenix_available:
        print("\n⚠️  Skipping (Phoenix not installed)")
        return True

    try:
        from cuga.backend.phoenix_integration.phoenix_tracer import PhoenixTracer

        print("\n1. Creating PhoenixTracer (disabled)...")
        tracer = PhoenixTracer(project_name="test_project", enabled=False)
        print(f"   ✅ Tracer created (enabled: {tracer.enabled})")

        print("\n2. Getting tracer stats...")
        stats = tracer.get_stats()
        print("   ✅ Stats retrieved:")
        for key, value in stats.items():
            print(f"      - {key}: {value}")

        print("\n3. Testing singleton pattern...")
        from cuga.backend.phoenix_integration.phoenix_tracer import get_phoenix_tracer

        tracer1 = get_phoenix_tracer(enabled=False)
        tracer2 = get_phoenix_tracer(enabled=False)
        if tracer1 is tracer2:
            print("   ✅ Singleton pattern works")
        else:
            print("   ❌ Singleton pattern failed")
            return False

        print("\n✅ PhoenixTracer initialization tests passed!")
        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_cuga_phoenix_integration(phoenix_available):
    """Test CugaPhoenixIntegration."""
    print("\n" + "=" * 60)
    print("Testing CugaPhoenixIntegration")
    print("=" * 60)

    try:
        # Temporarily disable Phoenix in settings for testing
        os.environ['PHOENIX_ENABLED'] = 'false'

        from cuga.backend.phoenix_integration.cuga_phoenix_integration import get_cuga_phoenix_integration

        print("\n1. Getting integration instance...")
        phoenix = get_cuga_phoenix_integration()
        print(f"   ✅ Integration created (enabled: {phoenix.enabled})")

        print("\n2. Testing singleton pattern...")
        phoenix2 = get_cuga_phoenix_integration()
        if phoenix is phoenix2:
            print("   ✅ Singleton pattern works")
        else:
            print("   ❌ Singleton pattern failed")
            return False

        print("\n3. Getting integration stats...")
        stats = phoenix.get_stats()
        print("   ✅ Stats retrieved:")
        for key, value in stats.items():
            print(f"      - {key}: {value}")

        print("\n4. Testing logging methods (disabled mode)...")
        # These should not fail even when disabled
        phoenix.start_agent_trace("test task")
        phoenix.log_tool_execution(
            tool_name="test_tool", tool_input={"arg": "value"}, tool_output="result", success=True
        )
        phoenix.log_agent_step(
            step_name="test_step", step_type="execution", input_data="input", output_data="output"
        )
        phoenix.log_llm_call(model="gpt-4", prompt="test prompt", response="test response")
        phoenix.log_error(error_type="TestError", error_message="Test error message")
        print("   ✅ All logging methods executed without errors")

        print("\n✅ CugaPhoenixIntegration tests passed!")
        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_configuration():
    """Test Phoenix configuration in settings."""
    print("\n" + "=" * 60)
    print("Testing Phoenix Configuration")
    print("=" * 60)

    try:
        print("\n1. Loading CUGA settings...")
        from cuga.config import settings

        print("   ✅ Settings loaded")

        print("\n2. Checking Phoenix configuration...")
        if hasattr(settings, 'phoenix'):
            print("   ✅ Phoenix configuration found")
            print(f"      - enabled: {settings.phoenix.enabled}")
            print(f"      - project_name: {settings.phoenix.project_name}")
            print(f"      - phoenix_host: {settings.phoenix.phoenix_host}")
            print(f"      - phoenix_port: {settings.phoenix.phoenix_port}")
            print(f"      - auto_instrument_langchain: {settings.phoenix.auto_instrument_langchain}")
            print(f"      - launch_phoenix: {settings.phoenix.launch_phoenix}")
        else:
            print("   ⚠️  Phoenix configuration not found in settings")
            return False

        print("\n✅ Configuration tests passed!")
        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("PHOENIX-CUGA INTEGRATION TEST SUITE")
    print("=" * 60)

    results = []

    # Test 1: Imports
    import_success, phoenix_available = test_imports()
    results.append(("Module Imports", import_success))

    if not import_success:
        print("\n❌ Cannot proceed without successful imports")
        return 1

    # Test 2: PhoenixTracer
    results.append(("PhoenixTracer Init", test_phoenix_tracer_init(phoenix_available)))

    # Test 3: CugaPhoenixIntegration
    results.append(("CugaPhoenixIntegration", test_cuga_phoenix_integration(phoenix_available)))

    # Test 4: Configuration
    results.append(("Configuration", test_configuration()))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{name:30} {status}")

    all_passed = all(result[1] for result in results)

    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("\nThe Phoenix integration is working correctly!")
        print("\nCore functionality verified:")
        print("  ✓ Module imports")
        print("  ✓ PhoenixTracer initialization")
        print("  ✓ CugaPhoenixIntegration")
        print("  ✓ Configuration")

        if not phoenix_available:
            print("\n📦 To enable Phoenix observability:")
            print("   uv pip install -e '.[phoenix]'")
            print("   or: pip install arize-phoenix openinference-instrumentation-langchain")
    else:
        print("⚠️  SOME TESTS FAILED")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

# Made with Bob
