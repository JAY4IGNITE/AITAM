from typing import List, Dict, Any
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import numpy as np
from ..models.dataset import LabelType

def compute_metrics(y_true: List[str], y_pred: List[str], labels: List[str]) -> Dict[str, Any]:
    """
    Computes standard evaluation metrics.
    labels should be the list of possible classes in order (e.g. ['BENIGN', 'MALICIOUS', 'PHISHING', 'SUSPICIOUS', 'SPAM']).
    """
    if not y_true or not y_pred:
        return {}
        
    # Calculate global metrics (macro averaged for multiclass)
    accuracy = accuracy_score(y_true, y_pred)
    precision = precision_score(y_true, y_pred, labels=labels, average='macro', zero_division=0)
    recall = recall_score(y_true, y_pred, labels=labels, average='macro', zero_division=0)
    f1 = f1_score(y_true, y_pred, labels=labels, average='macro', zero_division=0)
    
    # Calculate confusion matrix
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    cm_dict = {
        "labels": labels,
        "matrix": cm.tolist()
    }
    
    # Binary metrics approximation (Benign vs All Threat classes)
    y_true_bin = [0 if y == "BENIGN" else 1 for y in y_true]
    y_pred_bin = [0 if y == "BENIGN" else 1 for y in y_pred]
    
    try:
        tn, fp, fn, tp = confusion_matrix(y_true_bin, y_pred_bin, labels=[0, 1]).ravel()
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0
    except ValueError:
        fpr, fnr = 0.0, 0.0
        
    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "false_positive_rate": fpr,
        "false_negative_rate": fnr,
        "confusion_matrix": cm_dict
    }

def calculate_baseline(content: str) -> str:
    """A simplistic regex/heuristic baseline for comparison."""
    content_lower = content.lower()
    
    malicious_keywords = ["urgent", "login", "crypto", "verify", "password", "account suspended"]
    spam_keywords = ["winner", "lottery", "cash", "viagra", "buy now"]
    
    if any(k in content_lower for k in malicious_keywords):
        return "PHISHING"
    if any(k in content_lower for k in spam_keywords):
        return "SPAM"
        
    return "BENIGN"
