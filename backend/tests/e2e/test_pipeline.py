import requests
import time
import pytest

API_URL = "http://127.0.0.1:8000/api"

def test_full_autonomous_soc_pipeline():
    """
    End-to-end test of the entire autonomous pipeline.
    This test verifies:
    1. System Health API
    2. Input Processing & Investigation Creation
    3. Multi-Agent Triage (Priority calculation)
    4. Multi-Agent Investigation Planner
    5. Agent Execution (URL, Threat Intel)
    6. Risk Calculation
    7. Incident Creation
    8. Response Recommendation
    9. Human Approval Workflow
    10. Report Generation
    """
    
    # 1. Health Check
    health_resp = requests.get(f"{API_URL}/health")
    assert health_resp.status_code == 200, "Health check failed"
    health_data = health_resp.json()
    assert health_data["status"] in ["healthy", "degraded"], "System completely offline"
    
    # 2. Reset Demo State (Ensure clean slate for this target if it existed)
    reset_resp = requests.post(f"{API_URL}/demo/reset")
    assert reset_resp.status_code == 200, "Failed to reset demo data"
    
    # 3. Create Investigation with a suspicious phishing target
    payload = {
        "input_type": "URL",
        "target": "http://malicious-phishing.top/login/verify"
    }
    
    start_resp = requests.post(f"{API_URL}/investigations/analyze", json=payload)
    if start_resp.status_code != 200:
        print("ERROR:", start_resp.text)
    assert start_resp.status_code == 200, "Failed to start investigation"
    start_data = start_resp.json()
    
    assert "investigation_id" in start_data, "Missing investigation ID in response"
    inv_id = start_data["investigation_id"]
    
    print(f"\n[+] Started E2E Investigation: {inv_id}")
    
    # Poll until complete (Max 60 seconds)
    max_retries = 30
    inv_data = None
    
    for i in range(max_retries):
        resp = requests.get(f"{API_URL}/investigations/{inv_id}")
        assert resp.status_code == 200, "Failed to fetch investigation status"
        inv_data = resp.json()
        
        if inv_data["status"] in ["COMPLETED", "FAILED"]:
            break
            
        time.sleep(2)
        
    # 4. Verify Investigation completed successfully
    assert inv_data is not None, "Investigation data is None"
    assert inv_data["status"] == "COMPLETED", f"Investigation failed or timed out: {inv_data['status']}"
    
    # 5. Verify Agents executed
    agents_resp = requests.get(f"{API_URL}/investigations/{inv_id}/agents")
    assert agents_resp.status_code == 200, "Failed to fetch agent tasks"
    agents = agents_resp.json()
    
    assert len(agents) > 0, "No agents were scheduled or executed"
    for agent in agents:
        assert agent["status"] in ["COMPLETED", "FAILED"], f"Agent {agent['agent_name']} did not complete properly."
    
    # Check if specific intelligence was routed
    agent_names = [a["agent_name"] for a in agents]
    assert "threat_intelligence" in agent_names, f"Threat Intelligence Agent was not triggered. Found: {agent_names}"

    # 6. Verify Threat Intel Graph extraction
    intel_resp = requests.get(f"{API_URL}/investigations/{inv_id}/threat-intelligence")
    assert intel_resp.status_code == 200
    intel_data = intel_resp.json()
    assert isinstance(intel_data, list), "Threat intel should be a list"
    
    # 7. Verify Risk Score Computation
    risk_resp = requests.get(f"{API_URL}/investigations/{inv_id}/risk")
    assert risk_resp.status_code == 200, "Failed to fetch risk score"
    risk_data = risk_resp.json()
    
    assert "score" in risk_data, "Risk payload missing score"
    assert "level" in risk_data, "Risk payload missing level"
    assert risk_data["level"] in ["SAFE", "LOW", "MEDIUM", "HIGH", "CRITICAL"], "Invalid risk level string"

    # 8. Verify Incident Generation if high risk or verify incidents endpoint
    incidents_resp = requests.get(f"{API_URL}/incidents/")
    assert incidents_resp.status_code == 200, "Failed to fetch incidents"
    incidents = incidents_resp.json()
    
    # Find incident for this investigation if created
    incident = next((i for i in incidents if i["investigation_id"] == inv_id), None)
    if incident:
        assert incident["status"] == "INVESTIGATING", "Incident status should be INVESTIGATING"
        
        # 9. Verify Response Recommendations
        actions_resp = requests.get(f"{API_URL}/incidents/{incident['id']}")
        assert actions_resp.status_code == 200, "Failed to fetch incident details"
        actions = actions_resp.json().get("recommended_actions", [])
        
        block_action = next((a for a in actions if a["action_type"] == "BLOCK" or a["status"] == "PENDING_APPROVAL"), None)
        if block_action:
            # 10. Verify Human Approval Workflow
            approve_resp = requests.post(
                f"{API_URL}/incidents/{incident['id']}/approve-action",
                json={"action_id": block_action['id'], "analyst_id": "SOC-ANALYZER-01"}
            )
            assert approve_resp.status_code == 200, "Failed to approve response action"
            
            actions_resp_after = requests.get(f"{API_URL}/incidents/{incident['id']}")
            block_action_after = next((a for a in actions_resp_after.json().get("recommended_actions", []) if a["id"] == block_action["id"]), None)
            assert block_action_after["status"] == "EXECUTED", "Action status did not update to EXECUTED after approval"

    # 11. Verify Report Generation
    report_resp = requests.get(f"{API_URL}/investigations/{inv_id}/report")
    assert report_resp.status_code == 200, "Failed to generate Threat Report"
    report_data = report_resp.json()
    
    assert "target" in report_data, "Report missing target"
    assert "final_risk_score" in report_data, "Report missing risk score"
    
    print("[+] All E2E assertions passed successfully!")

if __name__ == "__main__":
    test_full_autonomous_soc_pipeline()
