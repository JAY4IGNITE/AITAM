import pytest
from app.engine.metrics import compute_metrics, calculate_baseline

def test_metrics_computation():
    y_true = ["BENIGN", "MALICIOUS", "BENIGN", "PHISHING", "MALICIOUS"]
    y_pred = ["BENIGN", "BENIGN", "BENIGN", "PHISHING", "MALICIOUS"]
    labels = ["BENIGN", "MALICIOUS", "PHISHING"]
    
    metrics = compute_metrics(y_true, y_pred, labels)
    
    assert metrics["accuracy"] == 0.8
    assert "precision" in metrics
    assert "recall" in metrics
    assert "f1_score" in metrics
    
    # 1 False negative (MALICIOUS -> BENIGN)
    assert metrics["false_negative_rate"] > 0
    # 0 False positive
    assert metrics["false_positive_rate"] == 0.0
    
    cm = metrics["confusion_matrix"]
    assert cm["labels"] == labels
    assert len(cm["matrix"]) == 3

def test_baseline_heuristic():
    assert calculate_baseline("You have won the lottery! Click here.") == "SPAM"
    assert calculate_baseline("Please verify your account password immediately.") == "PHISHING"
    assert calculate_baseline("Welcome to the team newsletter.") == "BENIGN"
