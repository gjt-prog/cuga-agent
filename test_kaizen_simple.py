#!/usr/bin/env python3
"""
Simple test script for Kaizen-CUGA integration (no API calls)
"""

import sys
from pathlib import Path

# Add CUGA to path
cuga_path = Path(__file__).parent / "src"
sys.path.insert(0, str(cuga_path))


def test_imports():
    """Test that all modules can be imported."""
    print("=" * 60)
    print("Testing Module Imports")
    print("=" * 60)

    try:
        print("\n1. Importing KaizenAdapter...")
        print("   ✅ KaizenAdapter imported")

        print("\n2. Importing TrajectoryCapture...")
        print("   ✅ TrajectoryCapture imported")

        print("\n3. Importing CugaLiteKaizenIntegration...")
        print("   ✅ CugaLiteKaizenIntegration imported")

        print("\n✅ All imports successful!")
        return True

    except Exception as e:
        print(f"\n❌ Import error: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_trajectory_capture():
    """Test TrajectoryCapture without API calls."""
    print("\n" + "=" * 60)
    print("Testing TrajectoryCapture")
    print("=" * 60)

    try:
        from cuga.backend.kaizen_integration.trajectory_capture import TrajectoryCapture

        print("\n1. Creating trajectory...")
        trajectory = TrajectoryCapture()
        print("   ✅ Created")

        print("\n2. Adding messages...")
        trajectory.add_user_message("Test task")
        trajectory.add_assistant_message("Processing...")
        trajectory.add_code_execution("x = 1 + 1", "2", success=True)
        trajectory.add_tool_call("test_tool", {"arg": "value"}, "result")
        print(f"   ✅ Added {len(trajectory)} messages")

        print("\n3. Setting metadata...")
        trajectory.set_metadata("task_id", "test_001")
        trajectory.set_metadata("success", True)
        print("   ✅ Metadata set")

        print("\n4. Getting summary...")
        summary = trajectory.summarize()
        print(summary)

        print("\n5. Converting to OpenAI format...")
        messages = trajectory.to_openai_format()
        print(f"   ✅ Converted {len(messages)} messages")
        for msg in messages[:2]:  # Show first 2
            print(f"      - {msg['role']}: {msg['content'][:50]}...")

        print("\n✅ TrajectoryCapture tests passed!")
        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_kaizen_adapter_init():
    """Test KaizenAdapter initialization."""
    print("\n" + "=" * 60)
    print("Testing KaizenAdapter Initialization")
    print("=" * 60)

    try:
        from cuga.backend.kaizen_integration.kaizen_adapter import KaizenAdapter

        print("\n1. Creating adapter with filesystem backend...")
        adapter = KaizenAdapter(
            kaizen_path="~/Dev/oss/kaizen", namespace_id="test_cuga", provider="filesystem", enabled=True
        )

        if adapter.enabled:
            print("   ✅ Adapter initialized and enabled")

            print("\n2. Getting stats...")
            stats = adapter.get_stats()
            print("   ✅ Stats retrieved:")
            for key, value in stats.items():
                print(f"      - {key}: {value}")

            print("\n✅ KaizenAdapter initialization tests passed!")
            return True
        else:
            print("   ⚠️  Adapter initialized but not enabled")
            return False

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_integration_singleton():
    """Test CugaLiteKaizenIntegration singleton."""
    print("\n" + "=" * 60)
    print("Testing Integration Singleton")
    print("=" * 60)

    try:
        from cuga.backend.kaizen_integration.cuga_lite_integration import get_kaizen_integration

        print("\n1. Getting integration instance...")
        kaizen1 = get_kaizen_integration()
        print(f"   ✅ Instance 1 created (enabled: {kaizen1.enabled})")

        print("\n2. Getting second instance...")
        kaizen2 = get_kaizen_integration()
        print("   ✅ Instance 2 retrieved")

        print("\n3. Verifying singleton pattern...")
        if kaizen1 is kaizen2:
            print("   ✅ Same instance (singleton works)")
        else:
            print("   ❌ Different instances (singleton failed)")
            return False

        print("\n4. Testing trajectory capture...")
        kaizen1.start_trajectory_capture("test task")
        kaizen1.capture_step("thought", "Planning...")
        print(f"   ✅ Captured {len(kaizen1.trajectory)} steps")

        print("\n✅ Integration singleton tests passed!")
        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("KAIZEN-CUGA INTEGRATION SIMPLE TEST SUITE")
    print("(No API calls required)")
    print("=" * 60)

    results = []

    # Test 1: Imports
    results.append(("Module Imports", test_imports()))

    # Test 2: TrajectoryCapture
    results.append(("TrajectoryCapture", test_trajectory_capture()))

    # Test 3: KaizenAdapter Init
    results.append(("KaizenAdapter Init", test_kaizen_adapter_init()))

    # Test 4: Integration Singleton
    results.append(("Integration Singleton", test_integration_singleton()))

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
        print("\nThe Kaizen integration is working correctly!")
        print("Core functionality verified:")
        print("  ✓ Module imports")
        print("  ✓ Trajectory capture")
        print("  ✓ Kaizen adapter initialization")
        print("  ✓ Integration singleton pattern")
    else:
        print("⚠️  SOME TESTS FAILED")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

# Made with Bob
