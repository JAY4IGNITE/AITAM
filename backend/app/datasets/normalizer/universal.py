from typing import Dict, Any, Tuple
from ...models.investigation import InputType
from ...models.dataset import LabelType

def infer_input_type(content: str) -> InputType:
    content_lower = content.lower()
    if content_lower.startswith("http://") or content_lower.startswith("https://"):
        return InputType.URL
    if "from:" in content_lower and "subject:" in content_lower:
        return InputType.EMAIL
    if len(content) < 160 and not "http" in content_lower:
        return InputType.SMS # rough heuristic
    return InputType.URL # default to URL

def normalize_sample(raw_sample: Dict[str, Any]) -> Tuple[str, InputType, LabelType]:
    """
    Takes a raw dictionary sample (e.g. from CSV/JSON) and attempts to extract:
    content, input_type, and label.
    """
    
    # 1. Extract Content
    content = None
    content_keys = ["content", "url", "URL", "link", "message", "text", "email", "body"]
    for key in content_keys:
        if key in raw_sample and raw_sample[key]:
            content = str(raw_sample[key])
            break
            
    if not content:
        raise ValueError("Could not find content field in sample.")
        
    # 2. Extract Label
    label_val = None
    label_keys = ["label", "Label", "class", "Class", "type", "target", "category"]
    for key in label_keys:
        if key in raw_sample:
            label_val = str(raw_sample[key]).upper().strip()
            break
            
    if label_val in ["1", "TRUE", "MALICIOUS", "BAD", "PHISHING", "SPAM"]:
        label = LabelType.MALICIOUS
        if "PHISH" in label_val:
            label = LabelType.PHISHING
        elif "SPAM" in label_val:
            label = LabelType.SPAM
    else:
        label = LabelType.BENIGN
        
    # 3. Extract Input Type
    input_type_val = None
    type_keys = ["input_type", "type", "format"]
    for key in type_keys:
        if key in raw_sample and str(raw_sample[key]).upper() in [e.value for e in InputType]:
            input_type_val = InputType(str(raw_sample[key]).upper())
            break
            
    if not input_type_val:
        input_type_val = infer_input_type(content)
        
    return content, input_type_val, label
