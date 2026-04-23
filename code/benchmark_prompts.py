"""
Domain-Specific Code Generation Benchmark Prompts
===================================================
Each prompt includes:
- task_id: unique identifier
- domain: healthcare | finance | molecular_sim | legal
- subdomain: specific area within domain
- prompt: the code generation instruction
- test_code: Python test code to verify functional correctness
- reference_solution: gold-standard implementation
- domain_keywords: list of domain-specific terms/APIs that should appear
- compliance_checks: domain-specific quality/compliance requirements
- difficulty: easy | medium | hard
"""

BENCHMARK_PROMPTS = [
    # =========================================================================
    # HEALTHCARE SYSTEMS (10 tasks)
    # =========================================================================
    {
        "task_id": "health_001",
        "domain": "healthcare",
        "subdomain": "FHIR_interoperability",
        "difficulty": "medium",
        "prompt": (
            "Write a Python function `create_fhir_patient(first_name, last_name, birth_date, gender, mrn)` "
            "that creates a FHIR R4 Patient resource as a Python dictionary. The resource must include:\n"
            "- resourceType set to 'Patient'\n"
            "- A unique id (UUID4)\n"
            "- An identifier with system 'http://hospital.example.org/mrn' and the provided mrn value\n"
            "- name with given and family fields\n"
            "- birthDate in YYYY-MM-DD format\n"
            "- gender (must be one of: male, female, other, unknown)\n"
            "- A meta field with lastUpdated timestamp in ISO 8601 format\n"
            "The function should validate gender input and raise ValueError for invalid values."
        ),
        "test_code": """
import json
from datetime import datetime

result = create_fhir_patient("John", "Doe", "1990-05-15", "male", "MRN12345")
assert result["resourceType"] == "Patient"
assert result["name"][0]["family"] == "Doe"
assert result["name"][0]["given"] == ["John"]
assert result["birthDate"] == "1990-05-15"
assert result["gender"] == "male"
assert result["identifier"][0]["system"] == "http://hospital.example.org/mrn"
assert result["identifier"][0]["value"] == "MRN12345"
assert "id" in result
assert "meta" in result and "lastUpdated" in result["meta"]

# Test gender validation
try:
    create_fhir_patient("Jane", "Doe", "1990-01-01", "invalid_gender", "MRN999")
    assert False, "Should have raised ValueError"
except ValueError:
    pass

# Test all valid genders
for g in ["male", "female", "other", "unknown"]:
    r = create_fhir_patient("Test", "User", "2000-01-01", g, "MRN000")
    assert r["gender"] == g
print("PASSED")
""",
        "reference_solution": """
import uuid
from datetime import datetime, timezone

def create_fhir_patient(first_name, last_name, birth_date, gender, mrn):
    valid_genders = {"male", "female", "other", "unknown"}
    if gender not in valid_genders:
        raise ValueError(f"Invalid gender '{gender}'. Must be one of {valid_genders}")
    
    return {
        "resourceType": "Patient",
        "id": str(uuid.uuid4()),
        "meta": {
            "lastUpdated": datetime.now(timezone.utc).isoformat()
        },
        "identifier": [{
            "system": "http://hospital.example.org/mrn",
            "value": mrn
        }],
        "name": [{
            "family": last_name,
            "given": [first_name]
        }],
        "birthDate": birth_date,
        "gender": gender
    }
""",
        "domain_keywords": ["resourceType", "Patient", "identifier", "FHIR", "meta", "uuid", "birthDate"],
        "compliance_checks": [
            "uses_uuid_for_id",
            "validates_gender_enum",
            "fhir_compliant_structure",
            "iso8601_timestamps"
        ]
    },
    {
        "task_id": "health_002",
        "domain": "healthcare",
        "subdomain": "clinical_calculations",
        "difficulty": "easy",
        "prompt": (
            "Write a Python function `calculate_bmi(weight_kg, height_m)` that calculates Body Mass Index "
            "and returns a dictionary with keys 'bmi' (float rounded to 1 decimal), 'category' (string), "
            "and 'risk_level' (string). Categories: Underweight (<18.5), Normal (18.5-24.9), "
            "Overweight (25-29.9), Obese Class I (30-34.9), Obese Class II (35-39.9), Obese Class III (>=40). "
            "Risk levels: Low (Normal), Moderate (Underweight/Overweight), High (Obese I), "
            "Very High (Obese II/III). Validate inputs: weight must be >0 and <=500, "
            "height must be >0 and <=3.0. Raise ValueError with descriptive message for invalid inputs."
        ),
        "test_code": """
r = calculate_bmi(70, 1.75)
assert r["bmi"] == 22.9
assert r["category"] == "Normal"
assert r["risk_level"] == "Low"

r = calculate_bmi(50, 1.80)
assert r["category"] == "Underweight"
assert r["risk_level"] == "Moderate"

r = calculate_bmi(90, 1.70)
assert r["category"] == "Obese Class I"
assert r["risk_level"] == "High"

r = calculate_bmi(150, 1.70)
assert r["category"] == "Obese Class III"
assert r["risk_level"] == "Very High"

try:
    calculate_bmi(-5, 1.75)
    assert False
except ValueError:
    pass

try:
    calculate_bmi(70, 0)
    assert False
except ValueError:
    pass
print("PASSED")
""",
        "reference_solution": """
def calculate_bmi(weight_kg, height_m):
    if not (0 < weight_kg <= 500):
        raise ValueError(f"Weight must be between 0 and 500 kg, got {weight_kg}")
    if not (0 < height_m <= 3.0):
        raise ValueError(f"Height must be between 0 and 3.0 m, got {height_m}")
    
    bmi = round(weight_kg / (height_m ** 2), 1)
    
    if bmi < 18.5:
        category, risk = "Underweight", "Moderate"
    elif bmi < 25:
        category, risk = "Normal", "Low"
    elif bmi < 30:
        category, risk = "Overweight", "Moderate"
    elif bmi < 35:
        category, risk = "Obese Class I", "High"
    elif bmi < 40:
        category, risk = "Obese Class II", "Very High"
    else:
        category, risk = "Obese Class III", "Very High"
    
    return {"bmi": bmi, "category": category, "risk_level": risk}
""",
        "domain_keywords": ["bmi", "weight", "height", "obese", "underweight", "risk"],
        "compliance_checks": ["input_validation", "clinical_accuracy", "proper_categorization"]
    },
    {
        "task_id": "health_003",
        "domain": "healthcare",
        "subdomain": "medication_safety",
        "difficulty": "hard",
        "prompt": (
            "Write a Python class `MedicationInteractionChecker` that checks for drug-drug interactions. "
            "The constructor takes a dictionary of known interactions where keys are frozensets of two drug names "
            "(lowercase) and values are dicts with 'severity' (str: 'minor','moderate','major','contraindicated') "
            "and 'description' (str). Implement methods:\n"
            "1. `check_pair(drug_a, drug_b)` -> returns interaction dict or None\n"
            "2. `check_regimen(drug_list)` -> returns list of all pairwise interactions found\n"
            "3. `is_safe(drug_list, max_severity='moderate')` -> returns True if no interaction exceeds max_severity\n"
            "Drug names should be case-insensitive. The severity ordering is: minor < moderate < major < contraindicated."
        ),
        "test_code": """
interactions = {
    frozenset(["warfarin", "aspirin"]): {"severity": "major", "description": "Increased bleeding risk"},
    frozenset(["metformin", "contrast_dye"]): {"severity": "contraindicated", "description": "Risk of lactic acidosis"},
    frozenset(["lisinopril", "potassium"]): {"severity": "moderate", "description": "Hyperkalemia risk"},
    frozenset(["amoxicillin", "methotrexate"]): {"severity": "major", "description": "Increased methotrexate toxicity"},
}

checker = MedicationInteractionChecker(interactions)

# Test pair check
r = checker.check_pair("Warfarin", "ASPIRIN")
assert r is not None
assert r["severity"] == "major"

assert checker.check_pair("warfarin", "metformin") is None

# Test regimen check
results = checker.check_regimen(["warfarin", "aspirin", "lisinopril", "potassium"])
assert len(results) == 2  # warfarin-aspirin and lisinopril-potassium

# Test safety check
assert checker.is_safe(["lisinopril", "potassium"], max_severity="moderate") == True
assert checker.is_safe(["warfarin", "aspirin"], max_severity="moderate") == False
assert checker.is_safe(["metformin", "contrast_dye"], max_severity="major") == False
print("PASSED")
""",
        "reference_solution": """
from itertools import combinations

class MedicationInteractionChecker:
    SEVERITY_ORDER = {"minor": 0, "moderate": 1, "major": 2, "contraindicated": 3}
    
    def __init__(self, interactions):
        self.interactions = {
            frozenset(d.lower() for d in k): v 
            for k, v in interactions.items()
        }
    
    def check_pair(self, drug_a, drug_b):
        key = frozenset([drug_a.lower(), drug_b.lower()])
        return self.interactions.get(key)
    
    def check_regimen(self, drug_list):
        drug_list_lower = [d.lower() for d in drug_list]
        results = []
        for a, b in combinations(drug_list_lower, 2):
            interaction = self.check_pair(a, b)
            if interaction:
                results.append({
                    "drugs": (a, b),
                    **interaction
                })
        return results
    
    def is_safe(self, drug_list, max_severity="moderate"):
        max_level = self.SEVERITY_ORDER[max_severity]
        interactions = self.check_regimen(drug_list)
        return all(
            self.SEVERITY_ORDER[i["severity"]] <= max_level 
            for i in interactions
        )
""",
        "domain_keywords": ["interaction", "severity", "medication", "drug", "contraindicated", "combinations"],
        "compliance_checks": ["case_insensitive_matching", "severity_ordering", "comprehensive_pairwise_check", "safety_validation"]
    },
    {
        "task_id": "health_004",
        "domain": "healthcare",
        "subdomain": "ehr_data_processing",
        "difficulty": "medium",
        "prompt": (
            "Write a Python function `parse_hl7_message(raw_message)` that parses a simplified HL7 v2.x "
            "message string. HL7 messages use '\\r' (or '\\n') as segment separators, '|' as field separators, "
            "'^' as component separators. The function should return a dictionary where:\n"
            "- Keys are segment names (first field of each segment, e.g., 'MSH', 'PID', 'OBX')\n"
            "- Values are lists of fields (split by '|'), where each field containing '^' is further split into a list\n"
            "- If there are multiple segments of the same type, the value should be a list of segment field-lists\n"
            "Handle empty fields gracefully (empty string). Strip whitespace from all values."
        ),
        "test_code": """
msg = "MSH|^~\\\\&|HIS|Hospital|LAB|Lab|20230101120000||ADT^A01|MSG001|P|2.5\\rPID|||12345^^^MRN||Doe^John^M||19900515|M\\rOBX|1|NM|WBC||7.5|10*3/uL|4.5-11.0|N\\rOBX|2|NM|HGB||14.2|g/dL|12.0-17.5|N"

result = parse_hl7_message(msg)

assert "MSH" in result
assert "PID" in result
assert "OBX" in result

# PID should have patient name as components
pid_fields = result["PID"]
if isinstance(pid_fields[0], list):
    pid_fields = pid_fields[0]
# Field 5 (index 5) should be name with components
name_field = pid_fields[5]
assert isinstance(name_field, list)
assert name_field[0] == "Doe"
assert name_field[1] == "John"

# Multiple OBX segments
obx_data = result["OBX"]
assert isinstance(obx_data, list)
assert len(obx_data) == 2
print("PASSED")
""",
        "reference_solution": """
def parse_hl7_message(raw_message):
    segments = raw_message.replace('\\r', '\\n').split('\\n')
    segments = [s.strip() for s in segments if s.strip()]
    
    result = {}
    for segment in segments:
        fields = segment.split('|')
        seg_name = fields[0].strip()
        
        parsed_fields = []
        for field in fields:
            field = field.strip()
            if '^' in field:
                parsed_fields.append([c.strip() for c in field.split('^')])
            else:
                parsed_fields.append(field)
        
        if seg_name in result:
            existing = result[seg_name]
            if isinstance(existing[0], list) and len(existing) > 0 and isinstance(existing[0][0], list if isinstance(existing[0], list) else str):
                if not isinstance(existing[0], list) or (isinstance(existing[0], list) and not isinstance(existing[0][0], list)):
                    result[seg_name] = [existing, parsed_fields]
                else:
                    result[seg_name].append(parsed_fields)
            else:
                result[seg_name] = [existing, parsed_fields]
        else:
            result[seg_name] = parsed_fields
    
    return result
""",
        "domain_keywords": ["HL7", "segment", "MSH", "PID", "OBX", "field", "component"],
        "compliance_checks": ["hl7_structure_parsing", "component_separation", "multi_segment_handling", "whitespace_handling"]
    },
    {
        "task_id": "health_005",
        "domain": "healthcare",
        "subdomain": "hipaa_compliance",
        "difficulty": "hard",
        "prompt": (
            "Write a Python function `deidentify_patient_data(record)` that removes or masks HIPAA-defined "
            "Protected Health Information (PHI) from a patient record dictionary. The function should:\n"
            "1. Mask the following 18 HIPAA identifiers if present as keys (case-insensitive matching):\n"
            "   - 'name' -> 'REDACTED'\n"
            "   - 'ssn', 'social_security' -> 'XXX-XX-XXXX'\n"
            "   - 'phone', 'telephone', 'fax' -> 'XXX-XXX-XXXX'\n"
            "   - 'email' -> 'REDACTED@REDACTED.com'\n"
            "   - 'address', 'street', 'city', 'zip', 'zip_code' -> 'REDACTED'\n"
            "   - 'mrn', 'medical_record_number' -> 'REDACTED'\n"
            "   - 'dob', 'date_of_birth', 'birth_date' -> retain only year (e.g., '1990')\n"
            "   - 'ip_address' -> '0.0.0.0'\n"
            "2. Return a new dictionary (do not modify the original)\n"
            "3. Preserve all non-PHI fields unchanged\n"
            "4. Handle nested dictionaries recursively"
        ),
        "test_code": """
import copy

record = {
    "name": "John Doe",
    "ssn": "123-45-6789",
    "phone": "555-123-4567",
    "email": "john.doe@hospital.com",
    "dob": "1990-05-15",
    "address": "123 Main St",
    "zip": "90210",
    "ip_address": "192.168.1.1",
    "mrn": "MRN12345",
    "diagnosis": "Type 2 Diabetes",
    "lab_results": {"glucose": 126, "hba1c": 7.2},
    "emergency_contact": {"name": "Jane Doe", "phone": "555-987-6543"}
}

original = copy.deepcopy(record)
result = deidentify_patient_data(record)

# Original should be unchanged
assert record == original, "Original record was modified!"

# PHI fields should be masked
assert result["name"] == "REDACTED"
assert result["ssn"] == "XXX-XX-XXXX"
assert result["phone"] == "XXX-XXX-XXXX"
assert result["email"] == "REDACTED@REDACTED.com"
assert result["dob"] == "1990"
assert result["address"] == "REDACTED"
assert result["zip"] == "REDACTED"
assert result["ip_address"] == "0.0.0.0"
assert result["mrn"] == "REDACTED"

# Non-PHI should be preserved
assert result["diagnosis"] == "Type 2 Diabetes"
assert result["lab_results"]["glucose"] == 126

# Nested PHI should be masked
assert result["emergency_contact"]["name"] == "REDACTED"
assert result["emergency_contact"]["phone"] == "XXX-XXX-XXXX"
print("PASSED")
""",
        "reference_solution": """
import copy
import re

def deidentify_patient_data(record):
    PHI_MASKS = {
        'name': 'REDACTED',
        'ssn': 'XXX-XX-XXXX',
        'social_security': 'XXX-XX-XXXX',
        'phone': 'XXX-XXX-XXXX',
        'telephone': 'XXX-XXX-XXXX',
        'fax': 'XXX-XXX-XXXX',
        'email': 'REDACTED@REDACTED.com',
        'address': 'REDACTED',
        'street': 'REDACTED',
        'city': 'REDACTED',
        'zip': 'REDACTED',
        'zip_code': 'REDACTED',
        'mrn': 'REDACTED',
        'medical_record_number': 'REDACTED',
        'ip_address': '0.0.0.0',
    }
    DATE_FIELDS = {'dob', 'date_of_birth', 'birth_date'}
    
    def _mask(data):
        if not isinstance(data, dict):
            return data
        
        result = {}
        for key, value in data.items():
            key_lower = key.lower()
            if key_lower in PHI_MASKS:
                result[key] = PHI_MASKS[key_lower]
            elif key_lower in DATE_FIELDS:
                if isinstance(value, str) and len(value) >= 4:
                    result[key] = value[:4]
                else:
                    result[key] = 'REDACTED'
            elif isinstance(value, dict):
                result[key] = _mask(value)
            else:
                result[key] = copy.deepcopy(value)
        return result
    
    return _mask(record)
""",
        "domain_keywords": ["HIPAA", "PHI", "deidentify", "redact", "protected_health_information", "mask"],
        "compliance_checks": ["hipaa_18_identifiers", "recursive_masking", "immutable_input", "date_generalization"]
    },
    # =========================================================================
    # FINANCIAL ALGORITHMS (10 tasks)
    # =========================================================================
    {
        "task_id": "fin_001",
        "domain": "finance",
        "subdomain": "risk_management",
        "difficulty": "medium",
        "prompt": (
            "Write a Python function `calculate_var(returns, confidence_level=0.95, method='historical')` "
            "that calculates Value at Risk (VaR) for a portfolio. Parameters:\n"
            "- returns: list of float (daily returns as decimals, e.g., 0.02 for 2%)\n"
            "- confidence_level: float (default 0.95)\n"
            "- method: 'historical' or 'parametric'\n"
            "For historical VaR, use the percentile method. For parametric VaR, assume normal distribution.\n"
            "Return a dictionary with keys: 'var' (float, positive number representing loss), "
            "'method' (str), 'confidence_level' (float), 'n_observations' (int).\n"
            "Raise ValueError if returns is empty or confidence_level not in (0,1).\n"
            "Use only the math and statistics standard library modules (no numpy)."
        ),
        "test_code": """
import math

returns = [-0.02, 0.01, -0.03, 0.02, -0.01, 0.03, -0.04, 0.01, -0.02, 0.02,
           -0.01, 0.015, -0.025, 0.005, -0.015, 0.01, -0.035, 0.02, -0.01, 0.025]

# Historical VaR
result = calculate_var(returns, 0.95, 'historical')
assert result['method'] == 'historical'
assert result['confidence_level'] == 0.95
assert result['n_observations'] == 20
assert result['var'] > 0  # VaR should be positive (represents loss)
assert 0.02 < result['var'] < 0.05  # reasonable range

# Parametric VaR
result2 = calculate_var(returns, 0.95, 'parametric')
assert result2['method'] == 'parametric'
assert result2['var'] > 0

# Input validation
try:
    calculate_var([], 0.95)
    assert False
except ValueError:
    pass

try:
    calculate_var(returns, 1.5)
    assert False
except ValueError:
    pass
print("PASSED")
""",
        "reference_solution": """
import math
import statistics

def calculate_var(returns, confidence_level=0.95, method='historical'):
    if not returns:
        raise ValueError("Returns list cannot be empty")
    if not (0 < confidence_level < 1):
        raise ValueError(f"Confidence level must be between 0 and 1, got {confidence_level}")
    if method not in ('historical', 'parametric'):
        raise ValueError(f"Method must be 'historical' or 'parametric', got {method}")
    
    sorted_returns = sorted(returns)
    n = len(returns)
    
    if method == 'historical':
        index = int((1 - confidence_level) * n)
        index = max(0, min(index, n - 1))
        var = -sorted_returns[index]
    else:
        mean = statistics.mean(returns)
        std = statistics.stdev(returns)
        z_score = statistics.NormalDist().inv_cdf(confidence_level)
        var = -(mean - z_score * std)
    
    return {
        'var': var,
        'method': method,
        'confidence_level': confidence_level,
        'n_observations': n
    }
""",
        "domain_keywords": ["VaR", "confidence", "percentile", "risk", "returns", "portfolio", "normal_distribution"],
        "compliance_checks": ["input_validation", "correct_var_formula", "positive_loss_convention", "method_selection"]
    },
    {
        "task_id": "fin_002",
        "domain": "finance",
        "subdomain": "portfolio_optimization",
        "difficulty": "hard",
        "prompt": (
            "Write a Python function `optimize_portfolio(expected_returns, cov_matrix, risk_free_rate=0.02)` "
            "that finds the Maximum Sharpe Ratio portfolio using a simple grid search approach.\n"
            "- expected_returns: list of expected returns for each asset\n"
            "- cov_matrix: list of lists (covariance matrix)\n"
            "- risk_free_rate: float\n"
            "Return a dictionary with: 'weights' (list of floats summing to 1.0), 'expected_return' (float), "
            "'volatility' (float), 'sharpe_ratio' (float).\n"
            "Constraints: all weights >= 0 (long-only), sum to 1.0.\n"
            "Use a grid search with step size 0.1 for 2-3 assets, or random sampling (10000 samples) for more.\n"
            "Use only standard library (math, random). Raise ValueError if dimensions don't match."
        ),
        "test_code": """
import math

# Simple 2-asset case
er = [0.10, 0.20]
cov = [[0.04, 0.006], [0.006, 0.09]]

result = optimize_portfolio(er, cov, 0.02)
assert abs(sum(result['weights']) - 1.0) < 0.01
assert all(w >= -0.01 for w in result['weights'])
assert result['sharpe_ratio'] > 0
assert result['expected_return'] > 0
assert result['volatility'] > 0

# 3-asset case
er3 = [0.08, 0.12, 0.15]
cov3 = [[0.04, 0.006, 0.002], [0.006, 0.09, 0.009], [0.002, 0.009, 0.16]]

result3 = optimize_portfolio(er3, cov3, 0.02)
assert abs(sum(result3['weights']) - 1.0) < 0.05
assert result3['sharpe_ratio'] > 0

# Dimension mismatch
try:
    optimize_portfolio([0.1, 0.2], [[0.04]], 0.02)
    assert False
except ValueError:
    pass
print("PASSED")
""",
        "reference_solution": """
import math
import random
from itertools import product

def optimize_portfolio(expected_returns, cov_matrix, risk_free_rate=0.02):
    n = len(expected_returns)
    if len(cov_matrix) != n or any(len(row) != n for row in cov_matrix):
        raise ValueError("Dimensions of expected_returns and cov_matrix must match")
    
    def portfolio_stats(weights):
        port_return = sum(w * r for w, r in zip(weights, expected_returns))
        port_var = sum(
            weights[i] * weights[j] * cov_matrix[i][j]
            for i in range(n) for j in range(n)
        )
        port_vol = math.sqrt(max(port_var, 1e-10))
        sharpe = (port_return - risk_free_rate) / port_vol if port_vol > 0 else 0
        return port_return, port_vol, sharpe
    
    best_sharpe = -float('inf')
    best_weights = [1/n] * n
    
    if n <= 3:
        steps = [i/10.0 for i in range(11)]
        for combo in product(steps, repeat=n):
            if abs(sum(combo) - 1.0) > 0.001:
                continue
            weights = list(combo)
            _, _, sharpe = portfolio_stats(weights)
            if sharpe > best_sharpe:
                best_sharpe = sharpe
                best_weights = weights
    else:
        random.seed(42)
        for _ in range(10000):
            raw = [random.random() for _ in range(n)]
            total = sum(raw)
            weights = [w/total for w in raw]
            _, _, sharpe = portfolio_stats(weights)
            if sharpe > best_sharpe:
                best_sharpe = sharpe
                best_weights = weights
    
    ret, vol, sharpe = portfolio_stats(best_weights)
    return {
        'weights': best_weights,
        'expected_return': ret,
        'volatility': vol,
        'sharpe_ratio': sharpe
    }
""",
        "domain_keywords": ["sharpe", "portfolio", "weights", "covariance", "volatility", "return", "risk_free"],
        "compliance_checks": ["long_only_constraint", "weights_sum_to_one", "sharpe_ratio_formula", "dimension_validation"]
    },
    {
        "task_id": "fin_003",
        "domain": "finance",
        "subdomain": "pricing_models",
        "difficulty": "medium",
        "prompt": (
            "Write a Python function `black_scholes(S, K, T, r, sigma, option_type='call')` "
            "that calculates the Black-Scholes option price. Parameters:\n"
            "- S: current stock price\n"
            "- K: strike price\n"
            "- T: time to expiration in years\n"
            "- r: risk-free interest rate (annual)\n"
            "- sigma: volatility (annual)\n"
            "- option_type: 'call' or 'put'\n"
            "Return a dictionary with: 'price' (float), 'delta' (float), 'd1' (float), 'd2' (float).\n"
            "Use the math and statistics standard library. Validate all inputs are positive (except r can be 0+)."
        ),
        "test_code": """
import math

result = black_scholes(100, 100, 1, 0.05, 0.2, 'call')
assert abs(result['price'] - 10.45) < 0.5  # approximate BS price
assert 0 < result['delta'] < 1
assert result['d1'] > result['d2']

# Put option (put-call parity check)
call = black_scholes(100, 100, 1, 0.05, 0.2, 'call')
put = black_scholes(100, 100, 1, 0.05, 0.2, 'put')
# C - P = S - K*e^(-rT)
parity = call['price'] - put['price']
expected_parity = 100 - 100 * math.exp(-0.05)
assert abs(parity - expected_parity) < 0.01

# Input validation
try:
    black_scholes(-100, 100, 1, 0.05, 0.2)
    assert False
except ValueError:
    pass
print("PASSED")
""",
        "reference_solution": """
import math
from statistics import NormalDist

def black_scholes(S, K, T, r, sigma, option_type='call'):
    if S <= 0 or K <= 0 or T <= 0 or sigma <= 0:
        raise ValueError("S, K, T, sigma must be positive")
    if r < 0:
        raise ValueError("Risk-free rate must be non-negative")
    if option_type not in ('call', 'put'):
        raise ValueError("option_type must be 'call' or 'put'")
    
    norm = NormalDist()
    d1 = (math.log(S/K) + (r + sigma**2/2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    
    if option_type == 'call':
        price = S * norm.cdf(d1) - K * math.exp(-r * T) * norm.cdf(d2)
        delta = norm.cdf(d1)
    else:
        price = K * math.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
        delta = norm.cdf(d1) - 1
    
    return {'price': price, 'delta': delta, 'd1': d1, 'd2': d2}
""",
        "domain_keywords": ["black_scholes", "d1", "d2", "strike", "volatility", "option", "delta", "NormalDist"],
        "compliance_checks": ["correct_bs_formula", "put_call_parity", "greeks_computation", "input_validation"]
    },
    {
        "task_id": "fin_004",
        "domain": "finance",
        "subdomain": "transaction_processing",
        "difficulty": "medium",
        "prompt": (
            "Write a Python class `AuditableTransaction` that represents a financial transaction with full audit trail. "
            "The constructor takes: amount (float), currency (str), sender (str), receiver (str), tx_type (str: 'credit'|'debit'|'transfer'). "
            "Implement:\n"
            "1. `validate()` -> returns (bool, list_of_errors). Check: amount > 0, currency is 3-letter uppercase, sender != receiver for transfers\n"
            "2. `to_ledger_entry()` -> returns dict with 'timestamp', 'tx_id' (UUID), 'amount', 'currency', 'sender', 'receiver', 'type', 'hash'\n"
            "3. The 'hash' should be SHA256 of '{tx_id}|{amount}|{currency}|{sender}|{receiver}|{timestamp}'\n"
            "4. `__repr__` -> readable string representation\n"
            "Each transaction should be immutable after creation (raise AttributeError on attribute modification)."
        ),
        "test_code": """
import hashlib

tx = AuditableTransaction(1000.50, "USD", "Alice", "Bob", "transfer")
valid, errors = tx.validate()
assert valid == True
assert errors == []

entry = tx.to_ledger_entry()
assert entry['amount'] == 1000.50
assert entry['currency'] == 'USD'
assert 'tx_id' in entry
assert 'timestamp' in entry
assert 'hash' in entry

# Verify hash integrity
expected = f"{entry['tx_id']}|{entry['amount']}|{entry['currency']}|{entry['sender']}|{entry['receiver']}|{entry['timestamp']}"
expected_hash = hashlib.sha256(expected.encode()).hexdigest()
assert entry['hash'] == expected_hash

# Validation failures
tx2 = AuditableTransaction(-100, "us", "Alice", "Alice", "transfer")
valid2, errors2 = tx2.validate()
assert valid2 == False
assert len(errors2) >= 3  # negative amount, bad currency, same sender/receiver

# Immutability
try:
    tx.amount = 9999
    assert False, "Should be immutable"
except AttributeError:
    pass

assert "1000.5" in repr(tx) or "1000.50" in repr(tx)
print("PASSED")
""",
        "reference_solution": """
import uuid
import hashlib
from datetime import datetime, timezone

class AuditableTransaction:
    def __init__(self, amount, currency, sender, receiver, tx_type):
        object.__setattr__(self, '_amount', amount)
        object.__setattr__(self, '_currency', currency)
        object.__setattr__(self, '_sender', sender)
        object.__setattr__(self, '_receiver', receiver)
        object.__setattr__(self, '_tx_type', tx_type)
        object.__setattr__(self, '_tx_id', str(uuid.uuid4()))
        object.__setattr__(self, '_timestamp', datetime.now(timezone.utc).isoformat())
    
    def __setattr__(self, name, value):
        raise AttributeError("Transaction is immutable")
    
    @property
    def amount(self): return self._amount
    @property
    def currency(self): return self._currency
    @property
    def sender(self): return self._sender
    @property
    def receiver(self): return self._receiver
    @property
    def tx_type(self): return self._tx_type
    
    def validate(self):
        errors = []
        if self._amount <= 0:
            errors.append("Amount must be positive")
        if not (len(self._currency) == 3 and self._currency.isupper()):
            errors.append("Currency must be 3-letter uppercase code")
        if self._tx_type == 'transfer' and self._sender == self._receiver:
            errors.append("Sender and receiver must differ for transfers")
        if self._tx_type not in ('credit', 'debit', 'transfer'):
            errors.append("Invalid transaction type")
        return (len(errors) == 0, errors)
    
    def to_ledger_entry(self):
        entry = {
            'tx_id': self._tx_id,
            'timestamp': self._timestamp,
            'amount': self._amount,
            'currency': self._currency,
            'sender': self._sender,
            'receiver': self._receiver,
            'type': self._tx_type,
        }
        hash_input = f"{self._tx_id}|{self._amount}|{self._currency}|{self._sender}|{self._receiver}|{self._timestamp}"
        entry['hash'] = hashlib.sha256(hash_input.encode()).hexdigest()
        return entry
    
    def __repr__(self):
        return f"AuditableTransaction({self._amount} {self._currency}, {self._sender}->{self._receiver}, {self._tx_type})"
""",
        "domain_keywords": ["audit", "ledger", "sha256", "hash", "uuid", "transaction", "immutable"],
        "compliance_checks": ["audit_trail", "hash_integrity", "immutability", "input_validation", "iso_timestamp"]
    },
    {
        "task_id": "fin_005",
        "domain": "finance",
        "subdomain": "monte_carlo_simulation",
        "difficulty": "hard",
        "prompt": (
            "Write a Python function `monte_carlo_option_price(S0, K, T, r, sigma, n_simulations=10000, n_steps=252, seed=42)` "
            "that prices a European call option using Monte Carlo simulation with Geometric Brownian Motion.\n"
            "- Use the GBM formula: S(t+dt) = S(t) * exp((r - sigma^2/2)*dt + sigma*sqrt(dt)*Z) where Z ~ N(0,1)\n"
            "- Return dict with: 'price' (discounted average payoff), 'std_error' (standard error of price estimate), "
            "'confidence_interval_95' (tuple of lower, upper), 'n_simulations' (int)\n"
            "- Use only math, random, and statistics modules\n"
            "- Set the random seed for reproducibility"
        ),
        "test_code": """
import math

result = monte_carlo_option_price(100, 100, 1, 0.05, 0.2, n_simulations=50000, seed=42)

# Price should be close to BS price (~10.45 for these params)
assert 8.5 < result['price'] < 12.5, f"Price {result['price']} out of expected range"
assert result['std_error'] > 0
assert result['std_error'] < 1.0  # should be reasonably small with 50k sims
assert result['confidence_interval_95'][0] < result['price'] < result['confidence_interval_95'][1]
assert result['n_simulations'] == 50000

# More simulations should give smaller std error
result2 = monte_carlo_option_price(100, 100, 1, 0.05, 0.2, n_simulations=100, seed=42)
assert result2['std_error'] > result['std_error']
print("PASSED")
""",
        "reference_solution": """
import math
import random
import statistics

def monte_carlo_option_price(S0, K, T, r, sigma, n_simulations=10000, n_steps=252, seed=42):
    random.seed(seed)
    dt = T / n_steps
    payoffs = []
    
    for _ in range(n_simulations):
        S = S0
        for _ in range(n_steps):
            Z = random.gauss(0, 1)
            S = S * math.exp((r - 0.5 * sigma**2) * dt + sigma * math.sqrt(dt) * Z)
        payoff = max(S - K, 0)
        payoffs.append(payoff)
    
    discount = math.exp(-r * T)
    discounted_payoffs = [p * discount for p in payoffs]
    price = statistics.mean(discounted_payoffs)
    std_dev = statistics.stdev(discounted_payoffs)
    std_error = std_dev / math.sqrt(n_simulations)
    
    ci_lower = price - 1.96 * std_error
    ci_upper = price + 1.96 * std_error
    
    return {
        'price': price,
        'std_error': std_error,
        'confidence_interval_95': (ci_lower, ci_upper),
        'n_simulations': n_simulations
    }
""",
        "domain_keywords": ["monte_carlo", "GBM", "simulation", "payoff", "discount", "confidence_interval", "std_error"],
        "compliance_checks": ["gbm_formula", "discounting", "confidence_interval", "reproducible_seed", "standard_error"]
    },
    # =========================================================================
    # MOLECULAR SIMULATION (10 tasks)
    # =========================================================================
    {
        "task_id": "mol_001",
        "domain": "molecular_sim",
        "subdomain": "molecular_representation",
        "difficulty": "medium",
        "prompt": (
            "Write a Python function `parse_smiles_basic(smiles)` that performs a simplified parse of a SMILES string. "
            "Return a dictionary with:\n"
            "- 'atoms': list of atom symbols found (e.g., ['C', 'C', 'O', 'N'])\n"
            "- 'bonds': list of tuples (atom_idx1, atom_idx2, bond_type) where bond_type is 'single', 'double', 'triple', or 'aromatic'\n"
            "- 'rings': number of ring closures detected (digits in SMILES)\n"
            "- 'branches': number of branches (parentheses pairs)\n"
            "- 'molecular_formula': dict of atom counts e.g., {'C': 2, 'O': 1}\n"
            "Handle: uppercase single atoms (C, N, O, S, P, F), two-letter atoms (Cl, Br), "
            "bond symbols (-, =, #), ring digits (0-9), and branches ().\n"
            "Ignore: H (implicit), charges, stereochemistry (@), isotopes."
        ),
        "test_code": """
# Ethanol: CCO
result = parse_smiles_basic("CCO")
assert result['atoms'] == ['C', 'C', 'O']
assert result['molecular_formula'] == {'C': 2, 'O': 1}
assert len(result['bonds']) == 2
assert result['rings'] == 0
assert result['branches'] == 0

# Acetic acid: CC(=O)O
result2 = parse_smiles_basic("CC(=O)O")
assert set(result2['atoms']) == {'C', 'C', 'O', 'O'} or result2['atoms'] == ['C', 'C', 'O', 'O']
assert result2['molecular_formula'] == {'C': 2, 'O': 2}
assert result2['branches'] == 1

# Benzene: c1ccccc1 or C1=CC=CC=C1
result3 = parse_smiles_basic("C1=CC=CC=C1")
assert result3['rings'] == 1
assert result3['molecular_formula'] == {'C': 6}

# Chloromethane: CCl
result4 = parse_smiles_basic("CCl")
assert 'Cl' in result4['atoms']
assert result4['molecular_formula'] == {'C': 1, 'Cl': 1}
print("PASSED")
""",
        "reference_solution": """
def parse_smiles_basic(smiles):
    atoms = []
    bonds = []
    ring_openings = {}
    branches = 0
    atom_stack = []
    current_bond = 'single'
    i = 0
    
    TWO_LETTER = {'Cl', 'Br'}
    SINGLE_ATOMS = {'C', 'N', 'O', 'S', 'P', 'F', 'I', 'B', 'c', 'n', 'o', 's'}
    BOND_MAP = {'-': 'single', '=': 'double', '#': 'triple', ':': 'aromatic'}
    
    ring_count = 0
    
    while i < len(smiles):
        ch = smiles[i]
        
        if i + 1 < len(smiles) and ch + smiles[i+1] in TWO_LETTER:
            atom = ch + smiles[i+1]
            atom_idx = len(atoms)
            atoms.append(atom)
            if atom_stack:
                bonds.append((atom_stack[-1], atom_idx, current_bond))
                current_bond = 'single'
            atom_stack.append(atom_idx)
            i += 2
            continue
        
        if ch.upper() in SINGLE_ATOMS:
            atom = ch.upper()
            atom_idx = len(atoms)
            atoms.append(atom)
            if atom_stack:
                bond_type = 'aromatic' if ch.islower() else current_bond
                bonds.append((atom_stack[-1], atom_idx, bond_type))
                current_bond = 'single'
            atom_stack.append(atom_idx)
            i += 1
            continue
        
        if ch in BOND_MAP:
            current_bond = BOND_MAP[ch]
            i += 1
            continue
        
        if ch.isdigit():
            digit = int(ch)
            if digit in ring_openings:
                bonds.append((ring_openings[digit], atom_stack[-1], current_bond))
                del ring_openings[digit]
                ring_count += 1
                current_bond = 'single'
            else:
                ring_openings[digit] = atom_stack[-1]
            i += 1
            continue
        
        if ch == '(':
            branches += 1
            atom_stack.append(atom_stack[-1])
            i += 1
            continue
        
        if ch == ')':
            atom_stack.pop()
            i += 1
            continue
        
        i += 1
    
    formula = {}
    for atom in atoms:
        formula[atom] = formula.get(atom, 0) + 1
    
    return {
        'atoms': atoms,
        'bonds': bonds,
        'rings': ring_count,
        'branches': branches,
        'molecular_formula': formula
    }
""",
        "domain_keywords": ["SMILES", "atoms", "bonds", "ring", "molecular_formula", "aromatic", "branch"],
        "compliance_checks": ["smiles_parsing", "atom_recognition", "bond_type_detection", "ring_detection", "formula_computation"]
    },
    {
        "task_id": "mol_002",
        "domain": "molecular_sim",
        "subdomain": "molecular_properties",
        "difficulty": "easy",
        "prompt": (
            "Write a Python function `calculate_molecular_weight(formula_str)` that calculates the molecular weight "
            "from a molecular formula string (e.g., 'H2O', 'C6H12O6', 'NaCl'). Use these atomic weights:\n"
            "H=1.008, He=4.003, Li=6.941, C=12.011, N=14.007, O=15.999, F=18.998, Na=22.990, "
            "P=30.974, S=32.065, Cl=35.453, K=39.098, Ca=40.078, Fe=55.845, Br=79.904, I=126.904.\n"
            "Return a dictionary with: 'molecular_weight' (float rounded to 3 decimals), "
            "'composition' (dict of element -> count), 'mass_fractions' (dict of element -> fraction).\n"
            "Raise ValueError for unknown elements."
        ),
        "test_code": """
result = calculate_molecular_weight("H2O")
assert abs(result['molecular_weight'] - 18.015) < 0.01
assert result['composition'] == {'H': 2, 'O': 1}
assert abs(result['mass_fractions']['H'] - 2*1.008/18.015) < 0.01
assert abs(result['mass_fractions']['O'] - 15.999/18.015) < 0.01

# Glucose
result2 = calculate_molecular_weight("C6H12O6")
assert abs(result2['molecular_weight'] - 180.156) < 0.1
assert result2['composition'] == {'C': 6, 'H': 12, 'O': 6}

# NaCl
result3 = calculate_molecular_weight("NaCl")
assert abs(result3['molecular_weight'] - 58.443) < 0.01

try:
    calculate_molecular_weight("Xx2")
    assert False
except ValueError:
    pass
print("PASSED")
""",
        "reference_solution": """
import re

def calculate_molecular_weight(formula_str):
    WEIGHTS = {
        'H': 1.008, 'He': 4.003, 'Li': 6.941, 'C': 12.011, 'N': 14.007,
        'O': 15.999, 'F': 18.998, 'Na': 22.990, 'P': 30.974, 'S': 32.065,
        'Cl': 35.453, 'K': 39.098, 'Ca': 40.078, 'Fe': 55.845, 'Br': 79.904,
        'I': 126.904
    }
    
    tokens = re.findall(r'([A-Z][a-z]?)(\d*)', formula_str)
    composition = {}
    
    for element, count in tokens:
        if not element:
            continue
        if element not in WEIGHTS:
            raise ValueError(f"Unknown element: {element}")
        count = int(count) if count else 1
        composition[element] = composition.get(element, 0) + count
    
    mw = sum(WEIGHTS[el] * cnt for el, cnt in composition.items())
    mass_fractions = {el: (WEIGHTS[el] * cnt) / mw for el, cnt in composition.items()}
    
    return {
        'molecular_weight': round(mw, 3),
        'composition': composition,
        'mass_fractions': mass_fractions
    }
""",
        "domain_keywords": ["molecular_weight", "atomic_weight", "formula", "composition", "mass_fraction"],
        "compliance_checks": ["correct_weights", "formula_parsing", "mass_fraction_calculation", "unknown_element_handling"]
    },
    {
        "task_id": "mol_003",
        "domain": "molecular_sim",
        "subdomain": "force_field_computation",
        "difficulty": "hard",
        "prompt": (
            "Write a Python function `lennard_jones_simulation(positions, epsilon=1.0, sigma=1.0, box_size=10.0, cutoff=2.5)` "
            "that computes Lennard-Jones forces and energy for a set of particles in a periodic box.\n"
            "- positions: list of [x, y, z] coordinates\n"
            "- Returns dict with: 'total_energy' (float), 'forces' (list of [fx,fy,fz] per particle), "
            "'pair_energies' (list of per-pair energies), 'n_pairs_in_cutoff' (int)\n"
            "- LJ potential: V(r) = 4*epsilon*((sigma/r)^12 - (sigma/r)^6)\n"
            "- LJ force magnitude: F(r) = 24*epsilon*(2*(sigma/r)^12 - (sigma/r)^6)/r\n"
            "- Apply minimum image convention for periodic boundaries\n"
            "- Only compute interactions within cutoff distance\n"
            "Use only math module."
        ),
        "test_code": """
import math

# Two particles at distance sigma -> energy should be 0 (LJ minimum is at 2^(1/6)*sigma)
pos = [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]]
result = lennard_jones_simulation(pos, epsilon=1.0, sigma=1.0, box_size=10.0)
# At r=sigma: V = 4*(1-1) = 0
assert abs(result['total_energy'] - 0.0) < 1e-10

# Two particles at distance 2^(1/6)*sigma -> minimum energy = -epsilon
r_min = 2**(1/6)
pos2 = [[0.0, 0.0, 0.0], [r_min, 0.0, 0.0]]
result2 = lennard_jones_simulation(pos2, epsilon=1.0, sigma=1.0, box_size=10.0)
assert abs(result2['total_energy'] - (-1.0)) < 0.01

# Test periodic boundary conditions
pos3 = [[0.5, 0.0, 0.0], [9.5, 0.0, 0.0]]
result3 = lennard_jones_simulation(pos3, epsilon=1.0, sigma=1.0, box_size=10.0)
# Minimum image distance should be 1.0, not 9.0
assert abs(result3['total_energy'] - 0.0) < 1e-10  # r=sigma -> V=0

# Forces should be equal and opposite (Newton's 3rd law)
assert len(result['forces']) == 2
for i in range(3):
    assert abs(result['forces'][0][i] + result['forces'][1][i]) < 1e-10
print("PASSED")
""",
        "reference_solution": """
import math

def lennard_jones_simulation(positions, epsilon=1.0, sigma=1.0, box_size=10.0, cutoff=2.5):
    n = len(positions)
    forces = [[0.0, 0.0, 0.0] for _ in range(n)]
    pair_energies = []
    total_energy = 0.0
    n_pairs = 0
    cutoff_sq = cutoff * cutoff * sigma * sigma
    
    for i in range(n):
        for j in range(i + 1, n):
            dx = positions[j][0] - positions[i][0]
            dy = positions[j][1] - positions[i][1]
            dz = positions[j][2] - positions[i][2]
            
            dx -= box_size * round(dx / box_size)
            dy -= box_size * round(dy / box_size)
            dz -= box_size * round(dz / box_size)
            
            r_sq = dx*dx + dy*dy + dz*dz
            
            if r_sq < cutoff_sq and r_sq > 1e-10:
                r = math.sqrt(r_sq)
                sr6 = (sigma / r) ** 6
                sr12 = sr6 * sr6
                
                energy = 4.0 * epsilon * (sr12 - sr6)
                total_energy += energy
                pair_energies.append(energy)
                n_pairs += 1
                
                force_mag = 24.0 * epsilon * (2.0 * sr12 - sr6) / r
                fx = force_mag * dx / r
                fy = force_mag * dy / r
                fz = force_mag * dz / r
                
                forces[i][0] -= fx
                forces[i][1] -= fy
                forces[i][2] -= fz
                forces[j][0] += fx
                forces[j][1] += fy
                forces[j][2] += fz
    
    return {
        'total_energy': total_energy,
        'forces': forces,
        'pair_energies': pair_energies,
        'n_pairs_in_cutoff': n_pairs
    }
""",
        "domain_keywords": ["lennard_jones", "sigma", "epsilon", "periodic", "minimum_image", "cutoff", "force"],
        "compliance_checks": ["lj_formula", "periodic_boundary", "minimum_image_convention", "newtons_third_law", "cutoff_applied"]
    },
    {
        "task_id": "mol_004",
        "domain": "molecular_sim",
        "subdomain": "drug_likeness",
        "difficulty": "medium",
        "prompt": (
            "Write a Python function `lipinski_rule_of_five(molecule)` that evaluates Lipinski's Rule of Five "
            "for drug-likeness. The input is a dictionary with keys: 'molecular_weight' (float), 'logP' (float), "
            "'h_bond_donors' (int), 'h_bond_acceptors' (int), 'rotatable_bonds' (int), 'psa' (float, polar surface area).\n"
            "Return a dictionary with:\n"
            "- 'passes_lipinski': bool (True if at most 1 violation of original 4 rules)\n"
            "- 'violations': list of strings describing each violation\n"
            "- 'n_violations': int\n"
            "- 'drug_likeness_score': float (0-1, fraction of rules passed)\n"
            "- 'veber_rules': dict with 'passes' (bool), 'details' (str) - Veber: rotatable_bonds <= 10 and PSA <= 140\n"
            "Rules: MW <= 500, LogP <= 5, HBD <= 5, HBA <= 10."
        ),
        "test_code": """
# Good drug candidate
mol1 = {
    'molecular_weight': 350.0, 'logP': 2.5, 'h_bond_donors': 2,
    'h_bond_acceptors': 5, 'rotatable_bonds': 4, 'psa': 80.0
}
r1 = lipinski_rule_of_five(mol1)
assert r1['passes_lipinski'] == True
assert r1['n_violations'] == 0
assert r1['drug_likeness_score'] == 1.0
assert r1['veber_rules']['passes'] == True

# Multiple violations
mol2 = {
    'molecular_weight': 600.0, 'logP': 7.0, 'h_bond_donors': 8,
    'h_bond_acceptors': 12, 'rotatable_bonds': 15, 'psa': 200.0
}
r2 = lipinski_rule_of_five(mol2)
assert r2['passes_lipinski'] == False
assert r2['n_violations'] == 4
assert r2['drug_likeness_score'] == 0.0
assert r2['veber_rules']['passes'] == False

# One violation (still passes)
mol3 = {
    'molecular_weight': 520.0, 'logP': 3.0, 'h_bond_donors': 2,
    'h_bond_acceptors': 5, 'rotatable_bonds': 6, 'psa': 90.0
}
r3 = lipinski_rule_of_five(mol3)
assert r3['passes_lipinski'] == True
assert r3['n_violations'] == 1
print("PASSED")
""",
        "reference_solution": """
def lipinski_rule_of_five(molecule):
    violations = []
    
    if molecule['molecular_weight'] > 500:
        violations.append(f"MW {molecule['molecular_weight']} > 500")
    if molecule['logP'] > 5:
        violations.append(f"LogP {molecule['logP']} > 5")
    if molecule['h_bond_donors'] > 5:
        violations.append(f"HBD {molecule['h_bond_donors']} > 5")
    if molecule['h_bond_acceptors'] > 10:
        violations.append(f"HBA {molecule['h_bond_acceptors']} > 10")
    
    n_violations = len(violations)
    passes = n_violations <= 1
    score = (4 - n_violations) / 4
    
    veber_pass = molecule['rotatable_bonds'] <= 10 and molecule['psa'] <= 140
    veber_details = []
    if molecule['rotatable_bonds'] > 10:
        veber_details.append(f"Rotatable bonds {molecule['rotatable_bonds']} > 10")
    if molecule['psa'] > 140:
        veber_details.append(f"PSA {molecule['psa']} > 140")
    
    return {
        'passes_lipinski': passes,
        'violations': violations,
        'n_violations': n_violations,
        'drug_likeness_score': score,
        'veber_rules': {
            'passes': veber_pass,
            'details': '; '.join(veber_details) if veber_details else 'All Veber rules satisfied'
        }
    }
""",
        "domain_keywords": ["lipinski", "drug_likeness", "molecular_weight", "logP", "h_bond", "Veber", "PSA"],
        "compliance_checks": ["lipinski_thresholds", "violation_counting", "veber_rules", "score_calculation"]
    },
    {
        "task_id": "mol_005",
        "domain": "molecular_sim",
        "subdomain": "energy_minimization",
        "difficulty": "hard",
        "prompt": (
            "Write a Python function `steepest_descent_minimizer(energy_func, grad_func, initial_coords, "
            "step_size=0.01, max_steps=1000, convergence=1e-6)` that performs energy minimization using "
            "steepest descent with adaptive step size.\n"
            "- energy_func(coords) -> float (energy)\n"
            "- grad_func(coords) -> list of floats (gradient, same length as coords)\n"
            "- initial_coords: list of floats\n"
            "Return dict with: 'final_coords' (list), 'final_energy' (float), 'n_steps' (int), "
            "'converged' (bool), 'energy_trajectory' (list of energies at each step), "
            "'gradient_norm_trajectory' (list of gradient norms).\n"
            "Adaptive step: if energy increases, halve the step size; if energy decreases for 5 consecutive steps, "
            "increase step by 1.2x. Convergence when gradient norm < convergence threshold."
        ),
        "test_code": """
import math

# Simple quadratic: f(x,y) = x^2 + y^2, minimum at (0,0)
def energy(coords):
    return coords[0]**2 + coords[1]**2

def grad(coords):
    return [2*coords[0], 2*coords[1]]

result = steepest_descent_minimizer(energy, grad, [5.0, 3.0], step_size=0.1, max_steps=1000)
assert result['converged'] == True
assert abs(result['final_coords'][0]) < 0.01
assert abs(result['final_coords'][1]) < 0.01
assert abs(result['final_energy']) < 0.001
assert result['n_steps'] > 0
assert len(result['energy_trajectory']) == result['n_steps'] + 1
assert result['energy_trajectory'][-1] < result['energy_trajectory'][0]

# Rosenbrock-like: f(x,y) = (1-x)^2 + 100*(y-x^2)^2
def rosenbrock_e(c):
    return (1-c[0])**2 + 100*(c[1]-c[0]**2)**2

def rosenbrock_g(c):
    dx = -2*(1-c[0]) - 400*c[0]*(c[1]-c[0]**2)
    dy = 200*(c[1]-c[0]**2)
    return [dx, dy]

result2 = steepest_descent_minimizer(rosenbrock_e, rosenbrock_g, [0.0, 0.0], step_size=0.001, max_steps=10000)
# May not converge to exact minimum with steepest descent, but energy should decrease
assert result2['energy_trajectory'][-1] < result2['energy_trajectory'][0]
print("PASSED")
""",
        "reference_solution": """
import math

def steepest_descent_minimizer(energy_func, grad_func, initial_coords, 
                                step_size=0.01, max_steps=1000, convergence=1e-6):
    coords = list(initial_coords)
    current_energy = energy_func(coords)
    energy_trajectory = [current_energy]
    gradient_norm_trajectory = []
    consecutive_decreases = 0
    
    for step in range(max_steps):
        gradient = grad_func(coords)
        grad_norm = math.sqrt(sum(g**2 for g in gradient))
        gradient_norm_trajectory.append(grad_norm)
        
        if grad_norm < convergence:
            return {
                'final_coords': coords,
                'final_energy': current_energy,
                'n_steps': step,
                'converged': True,
                'energy_trajectory': energy_trajectory,
                'gradient_norm_trajectory': gradient_norm_trajectory
            }
        
        new_coords = [c - step_size * g for c, g in zip(coords, gradient)]
        new_energy = energy_func(new_coords)
        
        if new_energy < current_energy:
            coords = new_coords
            current_energy = new_energy
            consecutive_decreases += 1
            if consecutive_decreases >= 5:
                step_size *= 1.2
                consecutive_decreases = 0
        else:
            step_size *= 0.5
            consecutive_decreases = 0
        
        energy_trajectory.append(current_energy)
    
    gradient = grad_func(coords)
    grad_norm = math.sqrt(sum(g**2 for g in gradient))
    gradient_norm_trajectory.append(grad_norm)
    
    return {
        'final_coords': coords,
        'final_energy': current_energy,
        'n_steps': max_steps,
        'converged': False,
        'energy_trajectory': energy_trajectory,
        'gradient_norm_trajectory': gradient_norm_trajectory
    }
""",
        "domain_keywords": ["minimization", "gradient", "steepest_descent", "convergence", "energy", "step_size", "adaptive"],
        "compliance_checks": ["gradient_descent", "adaptive_step_size", "convergence_criterion", "energy_decrease"]
    },
    # =========================================================================
    # LEGAL DOCUMENT PROCESSING (10 tasks)
    # =========================================================================
    {
        "task_id": "legal_001",
        "domain": "legal",
        "subdomain": "contract_analysis",
        "difficulty": "medium",
        "prompt": (
            "Write a Python function `extract_contract_clauses(contract_text)` that extracts and categorizes "
            "clauses from a legal contract text. Return a dictionary with:\n"
            "- 'clauses': list of dicts, each with 'number' (str), 'title' (str), 'text' (str), 'type' (str)\n"
            "- 'parties': list of party names identified\n"
            "- 'effective_date': str or None\n"
            "- 'termination_clause': dict or None (with 'notice_period' and 'conditions')\n"
            "Clause types: 'definition', 'obligation', 'termination', 'liability', 'confidentiality', "
            "'indemnification', 'governing_law', 'general'.\n"
            "Match clause types by keyword presence in title/text. "
            "Extract parties from the preamble (lines before first numbered clause). "
            "Look for dates in format 'Month Day, Year' or 'YYYY-MM-DD'."
        ),
        "test_code": """
contract = '''
AGREEMENT made as of January 15, 2024, between Acme Corp ("Seller") and Beta Inc ("Buyer").

1. DEFINITIONS
   1.1 "Product" means the software described in Exhibit A.
   1.2 "Confidential Information" means any proprietary data.

2. OBLIGATIONS
   2.1 Seller shall deliver the Product within 30 days.
   2.2 Buyer shall pay the agreed price upon delivery.

3. CONFIDENTIALITY
   Both parties agree to maintain strict confidentiality of all shared information.

4. TERMINATION
   Either party may terminate this agreement with 30 days written notice.
   Termination shall not affect any accrued rights or obligations.

5. GOVERNING LAW
   This agreement shall be governed by the laws of the State of Delaware.
'''

result = extract_contract_clauses(contract)
assert len(result['clauses']) >= 5
assert any(c['type'] == 'definition' for c in result['clauses'])
assert any(c['type'] == 'obligation' for c in result['clauses'])
assert any(c['type'] == 'confidentiality' for c in result['clauses'])
assert any(c['type'] == 'termination' for c in result['clauses'])
assert any(c['type'] == 'governing_law' for c in result['clauses'])
assert 'Acme Corp' in result['parties'] or 'Seller' in result['parties']
assert result['effective_date'] is not None
assert result['termination_clause'] is not None
print("PASSED")
""",
        "reference_solution": """
import re

def extract_contract_clauses(contract_text):
    lines = contract_text.strip().split('\\n')
    
    # Extract parties from preamble
    parties = []
    preamble_end = 0
    for i, line in enumerate(lines):
        if re.match(r'^\\s*\\d+\\.\\s', line):
            preamble_end = i
            break
        # Look for party patterns
        party_matches = re.findall(r'between\\s+(.+?)\\s+\\(', line, re.IGNORECASE)
        party_matches += re.findall(r'and\\s+(.+?)\\s+\\(', line, re.IGNORECASE)
        parties.extend([p.strip() for p in party_matches])
    
    # Extract dates
    date_pattern = r'((?:January|February|March|April|May|June|July|August|September|October|November|December)\\s+\\d{1,2},\\s+\\d{4}|\\d{4}-\\d{2}-\\d{2})'
    preamble = '\\n'.join(lines[:preamble_end])
    date_match = re.search(date_pattern, preamble)
    effective_date = date_match.group(1) if date_match else None
    
    # Extract clauses - ordered by specificity (most specific first)
    CLAUSE_TYPES_TITLE = {
        'definition': ['definition', 'defined terms'],
        'termination': ['termination', 'term and termination'],
        'governing_law': ['governing law', 'jurisdiction', 'applicable law', 'choice of law'],
        'confidentiality': ['confidential', 'non-disclosure', 'nda'],
        'indemnification': ['indemnif'],
        'liability': ['liability', 'limitation of liability'],
        'obligation': ['obligation', 'duties', 'responsibilities'],
    }
    CLAUSE_TYPES_BODY = {
        'definition': ['definition', 'defined', 'means'],
        'termination': ['terminat', 'expir', 'cancel'],
        'governing_law': ['governing law', 'governed by', 'jurisdiction'],
        'confidentiality': ['confidential', 'non-disclosure', 'secret'],
        'indemnification': ['indemnif', 'hold harmless'],
        'liability': ['liability', 'liable', 'damages'],
        'obligation': ['obligation'],
    }
    
    clause_pattern = re.compile(r'^\\s*(\\d+)\\.\\s+(.+)', re.MULTILINE)
    clauses = []
    matches = list(clause_pattern.finditer(contract_text))
    
    for idx, match in enumerate(matches):
        start = match.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(contract_text)
        
        number = match.group(1)
        title = match.group(2).strip()
        text = contract_text[start:end].strip()
        
        clause_type = 'general'
        title_lower = title.lower()
        # First try to match by title (most reliable)
        for ctype, keywords in CLAUSE_TYPES_TITLE.items():
            if any(kw in title_lower for kw in keywords):
                clause_type = ctype
                break
        # If no title match, try body keywords
        if clause_type == 'general':
            body_lower = text.lower()
            for ctype, keywords in CLAUSE_TYPES_BODY.items():
                if any(kw in body_lower for kw in keywords):
                    clause_type = ctype
                    break
        
        clauses.append({
            'number': number,
            'title': title,
            'text': text,
            'type': clause_type
        })
    
    # Extract termination details
    termination_clause = None
    for c in clauses:
        if c['type'] == 'termination':
            notice_match = re.search(r'(\\d+)\\s+days?\\s+(?:written\\s+)?notice', c['text'], re.IGNORECASE)
            termination_clause = {
                'notice_period': f"{notice_match.group(1)} days" if notice_match else None,
                'conditions': c['text']
            }
            break
    
    return {
        'clauses': clauses,
        'parties': parties,
        'effective_date': effective_date,
        'termination_clause': termination_clause
    }
""",
        "domain_keywords": ["clause", "contract", "party", "termination", "governing_law", "confidentiality", "obligation"],
        "compliance_checks": ["clause_extraction", "party_identification", "date_extraction", "clause_classification"]
    },
    {
        "task_id": "legal_002",
        "domain": "legal",
        "subdomain": "citation_processing",
        "difficulty": "medium",
        "prompt": (
            "Write a Python function `parse_legal_citation(citation_str)` that parses legal citations "
            "in common US legal citation formats. Support:\n"
            "1. Case law: 'Brown v. Board of Education, 347 U.S. 483 (1954)'\n"
            "2. Statute: '42 U.S.C. § 1983'\n"
            "3. Regulation: '17 C.F.R. § 240.10b-5'\n"
            "Return a dictionary with: 'type' ('case'|'statute'|'regulation'|'unknown'), "
            "'volume' (str), 'reporter' (str), 'page_or_section' (str), 'year' (str or None), "
            "'parties' (list for cases), 'full_citation' (original string), 'normalized' (standardized form)."
        ),
        "test_code": """
# Case citation
r1 = parse_legal_citation("Brown v. Board of Education, 347 U.S. 483 (1954)")
assert r1['type'] == 'case'
assert r1['volume'] == '347'
assert 'U.S.' in r1['reporter']
assert r1['page_or_section'] == '483'
assert r1['year'] == '1954'
assert 'Brown' in r1['parties']

# Statute
r2 = parse_legal_citation("42 U.S.C. § 1983")
assert r2['type'] == 'statute'
assert r2['volume'] == '42'
assert 'U.S.C.' in r2['reporter']
assert '1983' in r2['page_or_section']

# Regulation
r3 = parse_legal_citation("17 C.F.R. § 240.10b-5")
assert r3['type'] == 'regulation'
assert r3['volume'] == '17'
assert 'C.F.R.' in r3['reporter']

# All should have full_citation
assert r1['full_citation'] == "Brown v. Board of Education, 347 U.S. 483 (1954)"
print("PASSED")
""",
        "reference_solution": """
import re

def parse_legal_citation(citation_str):
    result = {
        'type': 'unknown',
        'volume': None,
        'reporter': None,
        'page_or_section': None,
        'year': None,
        'parties': [],
        'full_citation': citation_str,
        'normalized': citation_str.strip()
    }
    
    # Case law pattern: Parties, Volume Reporter Page (Year)
    case_pattern = r'^(.+?)\\s*,\\s*(\\d+)\\s+([A-Za-z\\.\\s]+?)\\s+(\\d+)\\s*\\((\\d{4})\\)'
    case_match = re.match(case_pattern, citation_str.strip())
    if case_match:
        parties_str = case_match.group(1)
        result['type'] = 'case'
        result['parties'] = [p.strip() for p in parties_str.split(' v. ')]
        result['volume'] = case_match.group(2)
        result['reporter'] = case_match.group(3).strip()
        result['page_or_section'] = case_match.group(4)
        result['year'] = case_match.group(5)
        result['normalized'] = f"{parties_str}, {result['volume']} {result['reporter']} {result['page_or_section']} ({result['year']})"
        return result
    
    # Statute pattern: Volume U.S.C. § Section
    statute_pattern = r'^(\\d+)\\s+(U\\.S\\.C\\.)\\s*§\\s*([\\d\\w\\.-]+)'
    statute_match = re.match(statute_pattern, citation_str.strip())
    if statute_match:
        result['type'] = 'statute'
        result['volume'] = statute_match.group(1)
        result['reporter'] = statute_match.group(2)
        result['page_or_section'] = statute_match.group(3)
        result['normalized'] = f"{result['volume']} {result['reporter']} § {result['page_or_section']}"
        return result
    
    # Regulation pattern: Volume C.F.R. § Section
    reg_pattern = r'^(\\d+)\\s+(C\\.F\\.R\\.)\\s*§\\s*([\\d\\w\\.-]+)'
    reg_match = re.match(reg_pattern, citation_str.strip())
    if reg_match:
        result['type'] = 'regulation'
        result['volume'] = reg_match.group(1)
        result['reporter'] = reg_match.group(2)
        result['page_or_section'] = reg_match.group(3)
        result['normalized'] = f"{result['volume']} {result['reporter']} § {result['page_or_section']}"
        return result
    
    return result
""",
        "domain_keywords": ["citation", "case", "statute", "regulation", "reporter", "U.S.C.", "C.F.R.", "section"],
        "compliance_checks": ["citation_format_recognition", "party_extraction", "volume_reporter_parsing", "bluebook_compliance"]
    },
    {
        "task_id": "legal_003",
        "domain": "legal",
        "subdomain": "compliance_checking",
        "difficulty": "hard",
        "prompt": (
            "Write a Python class `GDPRComplianceChecker` that analyzes data processing activities for GDPR compliance. "
            "Constructor takes a list of 'processing_activity' dicts, each with keys:\n"
            "- 'name' (str), 'purpose' (str), 'legal_basis' (str), 'data_categories' (list of str),\n"
            "- 'data_subjects' (list of str), 'retention_period_days' (int), 'has_consent' (bool),\n"
            "- 'has_dpia' (bool), 'cross_border_transfer' (bool), 'encryption' (bool)\n"
            "Implement methods:\n"
            "1. `check_activity(activity_name)` -> returns dict with 'compliant' (bool), 'issues' (list of str), 'risk_level' (str)\n"
            "2. `full_audit()` -> returns dict with 'total_activities', 'compliant_count', 'non_compliant', 'high_risk_activities', 'recommendations'\n"
            "3. `generate_record_of_processing()` -> returns list of dicts formatted as GDPR Article 30 records\n"
            "Risk levels: 'low', 'medium', 'high'. High risk if: special category data OR cross-border without DPIA OR no legal basis."
        ),
        "test_code": """
activities = [
    {
        'name': 'email_marketing',
        'purpose': 'Direct marketing communications',
        'legal_basis': 'consent',
        'data_categories': ['email', 'name'],
        'data_subjects': ['customers'],
        'retention_period_days': 365,
        'has_consent': True,
        'has_dpia': False,
        'cross_border_transfer': False,
        'encryption': True
    },
    {
        'name': 'health_monitoring',
        'purpose': 'Employee health tracking',
        'legal_basis': 'legitimate_interest',
        'data_categories': ['health_data', 'name', 'employee_id'],
        'data_subjects': ['employees'],
        'retention_period_days': 730,
        'has_consent': False,
        'has_dpia': False,
        'cross_border_transfer': True,
        'encryption': False
    },
    {
        'name': 'payroll',
        'purpose': 'Salary processing',
        'legal_basis': 'contract',
        'data_categories': ['name', 'bank_details', 'salary'],
        'data_subjects': ['employees'],
        'retention_period_days': 2555,
        'has_consent': False,
        'has_dpia': True,
        'cross_border_transfer': False,
        'encryption': True
    }
]

checker = GDPRComplianceChecker(activities)

# Email marketing should be compliant
r1 = checker.check_activity('email_marketing')
assert r1['compliant'] == True or len(r1['issues']) == 0
assert r1['risk_level'] == 'low'

# Health monitoring should have issues
r2 = checker.check_activity('health_monitoring')
assert r2['compliant'] == False
assert len(r2['issues']) > 0
assert r2['risk_level'] == 'high'  # special category data

# Full audit
audit = checker.full_audit()
assert audit['total_activities'] == 3
assert audit['compliant_count'] >= 1
assert len(audit['non_compliant']) >= 1
assert len(audit['recommendations']) > 0

# Record of processing
records = checker.generate_record_of_processing()
assert len(records) == 3
assert all('purpose' in r for r in records)
assert all('legal_basis' in r for r in records)
print("PASSED")
""",
        "reference_solution": """
class GDPRComplianceChecker:
    SPECIAL_CATEGORIES = {
        'health_data', 'biometric_data', 'genetic_data', 'racial_ethnic_origin',
        'political_opinions', 'religious_beliefs', 'trade_union_membership',
        'sexual_orientation', 'criminal_records'
    }
    VALID_LEGAL_BASES = {
        'consent', 'contract', 'legal_obligation', 'vital_interests',
        'public_task', 'legitimate_interest'
    }
    
    def __init__(self, activities):
        self.activities = {a['name']: a for a in activities}
    
    def check_activity(self, activity_name):
        a = self.activities[activity_name]
        issues = []
        risk_level = 'low'
        
        has_special = any(cat in self.SPECIAL_CATEGORIES for cat in a['data_categories'])
        
        if a['legal_basis'] not in self.VALID_LEGAL_BASES:
            issues.append(f"Invalid legal basis: {a['legal_basis']}")
            risk_level = 'high'
        
        if a['legal_basis'] == 'consent' and not a['has_consent']:
            issues.append("Legal basis is consent but consent not obtained")
        
        if has_special:
            risk_level = 'high'
            if not a['has_consent'] and a['legal_basis'] not in ('vital_interests', 'legal_obligation'):
                issues.append("Special category data requires explicit consent or specific legal basis")
            if not a['has_dpia']:
                issues.append("DPIA required for special category data processing")
        
        if a['cross_border_transfer']:
            if not a['has_dpia']:
                issues.append("Cross-border transfer requires DPIA")
                if risk_level != 'high':
                    risk_level = 'high'
            if not a['encryption']:
                issues.append("Cross-border transfer should use encryption")
        
        if not a['encryption'] and any(cat in ('bank_details', 'health_data', 'ssn') for cat in a['data_categories']):
            issues.append("Sensitive data should be encrypted")
        
        if a['retention_period_days'] > 365 * 5:
            issues.append("Retention period exceeds 5 years - review necessity")
            if risk_level == 'low':
                risk_level = 'medium'
        
        if not has_special and not a['cross_border_transfer'] and risk_level == 'low' and issues:
            risk_level = 'medium'
        
        return {
            'compliant': len(issues) == 0,
            'issues': issues,
            'risk_level': risk_level
        }
    
    def full_audit(self):
        results = {}
        non_compliant = []
        high_risk = []
        all_issues = []
        
        for name in self.activities:
            r = self.check_activity(name)
            results[name] = r
            if not r['compliant']:
                non_compliant.append(name)
            if r['risk_level'] == 'high':
                high_risk.append(name)
            all_issues.extend(r['issues'])
        
        recommendations = list(set(all_issues))
        
        return {
            'total_activities': len(self.activities),
            'compliant_count': len(self.activities) - len(non_compliant),
            'non_compliant': non_compliant,
            'high_risk_activities': high_risk,
            'recommendations': recommendations
        }
    
    def generate_record_of_processing(self):
        records = []
        for name, a in self.activities.items():
            records.append({
                'activity_name': name,
                'purpose': a['purpose'],
                'legal_basis': a['legal_basis'],
                'data_categories': a['data_categories'],
                'data_subjects': a['data_subjects'],
                'retention_period_days': a['retention_period_days'],
                'cross_border_transfer': a['cross_border_transfer'],
                'technical_measures': 'Encryption' if a['encryption'] else 'None specified',
                'dpia_conducted': a['has_dpia']
            })
        return records
""",
        "domain_keywords": ["GDPR", "compliance", "consent", "DPIA", "legal_basis", "data_categories", "special_category"],
        "compliance_checks": ["gdpr_article_6_legal_basis", "special_category_handling", "dpia_requirement", "article_30_records"]
    },
    {
        "task_id": "legal_004",
        "domain": "legal",
        "subdomain": "document_redaction",
        "difficulty": "medium",
        "prompt": (
            "Write a Python function `redact_legal_document(text, redaction_rules)` that redacts sensitive "
            "information from legal documents. Parameters:\n"
            "- text: the document text\n"
            "- redaction_rules: dict with keys being entity types and values being 'mask'|'remove'|'generalize'\n"
            "  Supported entity types: 'names', 'dates', 'amounts', 'addresses', 'phone_numbers', 'ssn', 'case_numbers'\n"
            "Return a dict with: 'redacted_text' (str), 'redactions' (list of dicts with 'original', 'replacement', 'type', 'position'),"
            " 'n_redactions' (int).\n"
            "Patterns: Names (capitalized words following Mr/Mrs/Ms/Dr or two consecutive capitalized words), "
            "Dates (MM/DD/YYYY, Month Day Year), Amounts ($X,XXX.XX), Phone (XXX-XXX-XXXX), SSN (XXX-XX-XXXX), "
            "Case numbers (XX-XXXX or Case No. XXXX).\n"
            "Mask: replace with [REDACTED_TYPE], Remove: delete entirely, Generalize: dates->year only, amounts->range."
        ),
        "test_code": """
text = \"\"\"
On 01/15/2024, Mr. John Smith filed Case No. 2024-1234 against Dr. Jane Williams.
The disputed amount was $150,000.00. Contact: 555-123-4567. SSN: 123-45-6789.
The hearing is at 100 Main Street, Springfield.
\"\"\"

rules = {
    'names': 'mask',
    'dates': 'generalize',
    'amounts': 'mask',
    'phone_numbers': 'mask',
    'ssn': 'mask',
    'case_numbers': 'mask'
}

result = redact_legal_document(text, rules)
assert '[REDACTED' in result['redacted_text'] or 'REDACTED' in result['redacted_text']
assert '123-45-6789' not in result['redacted_text']
assert '555-123-4567' not in result['redacted_text']
assert '$150,000.00' not in result['redacted_text']
assert result['n_redactions'] > 0
assert len(result['redactions']) == result['n_redactions']

# Each redaction should have required fields
for r in result['redactions']:
    assert 'original' in r
    assert 'replacement' in r
    assert 'type' in r
print("PASSED")
""",
        "reference_solution": """
import re

def redact_legal_document(text, redaction_rules):
    redactions = []
    redacted = text
    
    PATTERNS = {
        'ssn': r'\\b\\d{3}-\\d{2}-\\d{4}\\b',
        'phone_numbers': r'\\b\\d{3}-\\d{3}-\\d{4}\\b',
        'amounts': r'\\$[\\d,]+\\.?\\d*',
        'dates': r'\\b(?:\\d{1,2}/\\d{1,2}/\\d{4}|(?:January|February|March|April|May|June|July|August|September|October|November|December)\\s+\\d{1,2},?\\s+\\d{4})\\b',
        'case_numbers': r'(?:Case\\s+No\\.?\\s*)?\\b\\d{2,4}-\\d{2,6}\\b',
        'names': r'(?:Mr\\.?|Mrs\\.?|Ms\\.?|Dr\\.?)\\s+[A-Z][a-z]+(?:\\s+[A-Z][a-z]+)*',
    }
    
    for entity_type, action in redaction_rules.items():
        if entity_type not in PATTERNS:
            continue
        
        pattern = PATTERNS[entity_type]
        matches = list(re.finditer(pattern, redacted))
        
        offset = 0
        for match in matches:
            original = match.group()
            start = match.start() + offset
            end = match.end() + offset
            
            if action == 'mask':
                replacement = f'[REDACTED_{entity_type.upper()}]'
            elif action == 'remove':
                replacement = ''
            elif action == 'generalize':
                if entity_type == 'dates':
                    year_match = re.search(r'\\d{4}', original)
                    replacement = year_match.group() if year_match else '[REDACTED_DATE]'
                elif entity_type == 'amounts':
                    amt = float(original.replace('$', '').replace(',', ''))
                    if amt < 10000:
                        replacement = '$1,000-$10,000'
                    elif amt < 100000:
                        replacement = '$10,000-$100,000'
                    elif amt < 1000000:
                        replacement = '$100,000-$1,000,000'
                    else:
                        replacement = '$1,000,000+'
                else:
                    replacement = f'[REDACTED_{entity_type.upper()}]'
            else:
                replacement = f'[REDACTED_{entity_type.upper()}]'
            
            redacted = redacted[:start] + replacement + redacted[end:]
            offset += len(replacement) - (end - start - offset + offset)
            
            redactions.append({
                'original': original,
                'replacement': replacement,
                'type': entity_type,
                'position': match.start()
            })
    
    return {
        'redacted_text': redacted,
        'redactions': redactions,
        'n_redactions': len(redactions)
    }
""",
        "domain_keywords": ["redact", "REDACTED", "sensitive", "phi", "pii", "mask", "pattern", "regex"],
        "compliance_checks": ["pii_detection", "redaction_modes", "audit_trail_of_redactions", "pattern_coverage"]
    },
    {
        "task_id": "legal_005",
        "domain": "legal",
        "subdomain": "risk_assessment",
        "difficulty": "hard",
        "prompt": (
            "Write a Python class `LegalRiskAssessor` that evaluates legal risks in business documents. "
            "Constructor takes a list of 'risk_rules' dicts with: 'pattern' (regex str), 'risk_type' (str), "
            "'severity' (1-10), 'description' (str), 'recommendation' (str).\n"
            "Implement:\n"
            "1. `assess_document(text)` -> returns dict with 'risks' (list of matched risks), "
            "'overall_risk_score' (0-100), 'risk_level' (str: 'low'|'medium'|'high'|'critical'), "
            "'n_risks' (int)\n"
            "2. `compare_documents(text1, text2)` -> returns dict comparing risk profiles\n"
            "3. `generate_risk_report(text)` -> returns formatted string report\n"
            "Overall score: sum of severities * frequency, normalized to 0-100.\n"
            "Risk levels: low (0-25), medium (26-50), high (51-75), critical (76-100)."
        ),
        "test_code": """
rules = [
    {'pattern': r'(?i)unlimited\\s+liabilit', 'risk_type': 'liability', 'severity': 9, 
     'description': 'Unlimited liability clause detected', 'recommendation': 'Negotiate a liability cap'},
    {'pattern': r'(?i)indemnif', 'risk_type': 'indemnification', 'severity': 6, 
     'description': 'Indemnification clause present', 'recommendation': 'Review scope of indemnification'},
    {'pattern': r'(?i)auto.?renew', 'risk_type': 'renewal', 'severity': 4, 
     'description': 'Auto-renewal clause', 'recommendation': 'Set calendar reminder for opt-out'},
    {'pattern': r'(?i)non.?compete', 'risk_type': 'restriction', 'severity': 7, 
     'description': 'Non-compete restriction', 'recommendation': 'Verify enforceability and scope'},
]

assessor = LegalRiskAssessor(rules)

doc1 = "This agreement includes unlimited liability for the vendor. The vendor shall indemnify the client. This contract auto-renews annually."
r1 = assessor.assess_document(doc1)
assert r1['n_risks'] == 3
assert r1['overall_risk_score'] > 0
assert r1['risk_level'] in ('medium', 'high', 'critical')

doc2 = "Standard service agreement with limited liability of $10,000."
r2 = assessor.assess_document(doc2)
assert r2['n_risks'] == 0 or r2['overall_risk_score'] < r1['overall_risk_score']

# Compare
comparison = assessor.compare_documents(doc1, doc2)
assert 'doc1_score' in comparison
assert 'doc2_score' in comparison
assert comparison['doc1_score'] > comparison['doc2_score']

# Report
report = assessor.generate_risk_report(doc1)
assert isinstance(report, str)
assert len(report) > 50
print("PASSED")
""",
        "reference_solution": """
import re

class LegalRiskAssessor:
    def __init__(self, risk_rules):
        self.rules = risk_rules
    
    def assess_document(self, text):
        risks = []
        total_severity = 0
        max_possible = sum(r['severity'] for r in self.rules) * 2
        
        for rule in self.rules:
            matches = re.findall(rule['pattern'], text)
            if matches:
                frequency = len(matches)
                risks.append({
                    'risk_type': rule['risk_type'],
                    'severity': rule['severity'],
                    'frequency': frequency,
                    'description': rule['description'],
                    'recommendation': rule['recommendation']
                })
                total_severity += rule['severity'] * frequency
        
        if max_possible > 0:
            score = min(100, int((total_severity / max_possible) * 100))
        else:
            score = 0
        
        if score <= 25:
            level = 'low'
        elif score <= 50:
            level = 'medium'
        elif score <= 75:
            level = 'high'
        else:
            level = 'critical'
        
        return {
            'risks': risks,
            'overall_risk_score': score,
            'risk_level': level,
            'n_risks': len(risks)
        }
    
    def compare_documents(self, text1, text2):
        r1 = self.assess_document(text1)
        r2 = self.assess_document(text2)
        
        r1_types = {r['risk_type'] for r in r1['risks']}
        r2_types = {r['risk_type'] for r in r2['risks']}
        
        return {
            'doc1_score': r1['overall_risk_score'],
            'doc1_level': r1['risk_level'],
            'doc1_risks': r1['n_risks'],
            'doc2_score': r2['overall_risk_score'],
            'doc2_level': r2['risk_level'],
            'doc2_risks': r2['n_risks'],
            'shared_risks': list(r1_types & r2_types),
            'unique_to_doc1': list(r1_types - r2_types),
            'unique_to_doc2': list(r2_types - r1_types),
            'higher_risk': 'doc1' if r1['overall_risk_score'] > r2['overall_risk_score'] else 'doc2'
        }
    
    def generate_risk_report(self, text):
        assessment = self.assess_document(text)
        lines = [
            "=" * 60,
            "LEGAL RISK ASSESSMENT REPORT",
            "=" * 60,
            f"Overall Risk Score: {assessment['overall_risk_score']}/100",
            f"Risk Level: {assessment['risk_level'].upper()}",
            f"Total Risks Identified: {assessment['n_risks']}",
            "-" * 60,
        ]
        
        for i, risk in enumerate(assessment['risks'], 1):
            lines.extend([
                f"\\nRisk #{i}: {risk['risk_type'].upper()}",
                f"  Severity: {risk['severity']}/10",
                f"  Occurrences: {risk['frequency']}",
                f"  Description: {risk['description']}",
                f"  Recommendation: {risk['recommendation']}",
            ])
        
        lines.append("\\n" + "=" * 60)
        return "\\n".join(lines)
""",
        "domain_keywords": ["risk", "liability", "indemnification", "compliance", "severity", "assessment", "recommendation"],
        "compliance_checks": ["pattern_matching", "risk_scoring", "document_comparison", "report_generation"]
    },
]

if __name__ == "__main__":
    print(f"Total benchmark prompts: {len(BENCHMARK_PROMPTS)}")
    domains = {}
    for p in BENCHMARK_PROMPTS:
        d = p['domain']
        domains[d] = domains.get(d, 0) + 1
    for d, c in sorted(domains.items()):
        print(f"  {d}: {c} tasks")
