import sys
from backend import run_travel_agent, resume_travel_agent

print("=== Test 1: Guardrail Blocked (Non-travel request) ===")
res = run_travel_agent("Tell me a joke about programming")
print(f"Status: {res.get('status')}")
print(f"Content: {res.get('content')}")
print(f"Awaiting approval: {res.get('awaiting_approval')}")

print("\n=== Test 2: Valid Travel Request (Initiation & Pause) ===")
res2 = run_travel_agent("Plan a 3-day trip to Paris from London with $1500 budget")
thread_id = res2.get("thread_id")
print(f"Thread ID: {thread_id}")
print(f"Status: {res2.get('status')}")
print(f"Summary for Approval: {res2.get('content')}")
print(f"Awaiting approval: {res2.get('awaiting_approval')}")
print(f"Agents run: {res2.get('agents_run')}")

if res2.get('awaiting_approval'):
    print("\n=== Test 3: Resume Travel Request (Approve) ===")
    res3 = resume_travel_agent(thread_id, approved=True)
    print(f"Status: {res3.get('status')}")
    print(f"Awaiting approval: {res3.get('awaiting_approval')}")
    print(f"Final Response (truncated): {res3.get('content')[:150]}...")
