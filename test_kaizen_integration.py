#!/usr/bin/env python3
"""
Test script for Kaizen-CUGA integration

This script tests the basic functionality of the Kaizen integration
without requiring a full CUGA setup.
"""

import sys
import os
from pathlib import Path

# Add CUGA to path
cuga_path = Path(__file__).parent / "src"
sys.path.insert(0, str(cuga_path))


def test_kaizen_adapter():
    """Test KaizenAdapter initialization and basic operations."""
    print("=" * 60)
    print("Testing KaizenAdapter")
    print("=" * 60)

    try:
        from cuga.backend.kaizen_integration.kaizen_adapter import KaizenAdapter

        # Initialize adapter
        print("\n1. Initializing KaizenAdapter...")
        adapter = KaizenAdapter(
            kaizen_path="~/Dev/oss/kaizen", namespace_id="test_cuga_lite", provider="filesystem", enabled=True
        )

        if adapter.enabled:
            print("   ✅ Adapter initialized successfully")
        else:
            print("   ⚠️  Adapter initialization failed")
            return False

        # Add a test guideline
        print("\n2. Adding test guideline...")
        success = adapter.add_guideline(
            "Always validate input data before processing",
            metadata={"source": "test", "category": "data_validation"},
        )
        print(f"   {'✅' if success else '❌'} Guideline added: {success}")

        # Retrieve guidelines
        print("\n3. Retrieving guidelines...")
        guidelines = adapter.get_guidelines("validate data", limit=5)
        print(f"   ✅ Retrieved {len(guidelines)} guidelines")
        for i, guideline in enumerate(guidelines, 1):
            print(f"      {i}. {guideline[:80]}...")

        # Get stats
        print("\n4. Getting knowledge base stats...")
        stats = adapter.get_stats()
        print("   ✅ Stats retrieved:")
        print(f"      - Enabled: {stats.get('enabled')}")
        print(f"      - Namespace: {stats.get('namespace_id')}")
        print(f"      - Provider: {stats.get('provider')}")
        print(f"      - Guidelines: {stats.get('guidelines_count', 0)}")
        print(f"      - Trajectories: {stats.get('trajectories_count', 0)}")

        # Test trajectory saving
        print("\n5. Testing trajectory save...")
        test_messages = [
            {"role": "user", "content": "Calculate sum of numbers"},
            {"role": "assistant", "content": "I'll calculate the sum"},
            {"role": "assistant", "content": "```python\nresult = sum([1, 2, 3])\n```"},
            {"role": "system", "content": "Execution output: 6"},
        ]

        success = adapter.save_trajectory(
            messages=test_messages,
            task_id="test_task_001",
            generate_tips=False,  # Skip tip generation for speed
        )
        print(f"   {'✅' if success else '❌'} Trajectory saved: {success}")

        print("\n✅ All KaizenAdapter tests passed!")
        return True

    except Exception as e:
        print(f"\n❌ Error testing KaizenAdapter: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_trajectory_capture():
    """Test TrajectoryCapture functionality."""
    print("\n" + "=" * 60)
    print("Testing TrajectoryCapture")
    print("=" * 60)

    try:
        from cuga.backend.kaizen_integration.trajectory_capture import TrajectoryCapture

        print("\n1. Creating TrajectoryCapture...")
        trajectory = TrajectoryCapture()
        print("   ✅ TrajectoryCapture created")

        print("\n2. Adding messages...")
        trajectory.add_user_message("Calculate revenue")
        trajectory.add_assistant_message("I'll calculate the revenue")
        trajectory.add_code_execution(code="revenue = sum(sales)", output="Total: $50000", success=True)
        trajectory.add_tool_call(tool_name="get_sales_data", args={"year": 2024}, result={"total": 50000})
        print(f"   ✅ Added {len(trajectory)} messages")

        print("\n3. Setting metadata...")
        trajectory.set_metadata("task", "revenue_calculation")
        trajectory.set_metadata("success", True)
        print("   ✅ Metadata set")

        print("\n4. Getting trajectory summary...")
        summary = trajectory.summarize()
        print(summary)

        print("\n5. Converting to OpenAI format...")
        openai_messages = trajectory.to_openai_format()
        print(f"   ✅ Converted {len(openai_messages)} messages")

        print("\n✅ All TrajectoryCapture tests passed!")
        return True

    except Exception as e:
        print(f"\n❌ Error testing TrajectoryCapture: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_cuga_lite_integration():
    """Test CugaLiteKaizenIntegration."""
    print("\n" + "=" * 60)
    print("Testing CugaLiteKaizenIntegration")
    print("=" * 60)

    try:
        # Set environment variable for testing
        os.environ['KAIZEN_PROVIDER'] = 'filesystem'

        from cuga.backend.kaizen_integration.cuga_lite_integration import get_kaizen_integration

        print("\n1. Getting integration instance...")
        kaizen = get_kaizen_integration()
        print(f"   ✅ Integration enabled: {kaizen.enabled}")

        if not kaizen.enabled:
            print("   ⚠️  Integration not enabled, skipping tests")
            return True

        print("\n2. Testing guideline retrieval...")
        guidelines = kaizen.get_guidelines_for_task("process customer data")
        print(f"   ✅ Retrieved {len(guidelines)} guidelines")

        print("\n3. Testing guideline formatting...")
        formatted = kaizen.format_guidelines_for_prompt(guidelines)
        if formatted:
            print(f"   ✅ Formatted guidelines ({len(formatted)} chars)")
            print(formatted[:200] + "...")
        else:
            print("   ℹ️  No guidelines to format")

        print("\n4. Testing trajectory capture...")
        kaizen.start_trajectory_capture("test task")
        kaizen.capture_step("thought", "Planning the task")
        kaizen.capture_code_execution("x = 1 + 1", "2", success=True)
        kaizen.capture_tool_call("test_tool", {"arg": "value"}, "result")
        print("   ✅ Trajectory steps captured")

        print("\n5. Testing trajectory save...")
        saved = kaizen.save_trajectory(final_answer="Task completed", success=True)
        print(f"   {'✅' if saved else 'ℹ️ '} Trajectory save: {saved}")

        print("\n6. Getting integration stats...")
        stats = kaizen.get_stats()
        print("   ✅ Stats retrieved:")
        for key, value in stats.items():
            if key not in ['current_trajectory_metadata']:
                print(f"      - {key}: {value}")

        print("\n✅ All CugaLiteKaizenIntegration tests passed!")
        return True

    except Exception as e:
        print(f"\n❌ Error testing CugaLiteKaizenIntegration: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("KAIZEN-CUGA INTEGRATION TEST SUITE")
    print("=" * 60)

    results = []

    # Test 1: KaizenAdapter
    results.append(("KaizenAdapter", test_kaizen_adapter()))

    # Test 2: TrajectoryCapture
    results.append(("TrajectoryCapture", test_trajectory_capture()))

    # Test 3: CugaLiteKaizenIntegration
    results.append(("CugaLiteKaizenIntegration", test_cuga_lite_integration()))

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
    else:
        print("⚠️  SOME TESTS FAILED")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

# Made with Bob
