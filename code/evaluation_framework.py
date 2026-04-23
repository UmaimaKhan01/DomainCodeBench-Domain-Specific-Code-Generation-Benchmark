"""
Domain-Specific Code Generation Evaluation Framework
=====================================================
Evaluates code generation models across healthcare, finance, 
molecular simulation, and legal domains with multi-dimensional metrics.
"""

import json
import os
import re
import sys
import time
import hashlib
import traceback
import subprocess
import tempfile
import textwrap
from datetime import datetime, timezone
from collections import defaultdict

# ============================================================
# METRIC DEFINITIONS
# ============================================================

class DomainMetrics:
    """Computes domain-specific quality metrics beyond functional correctness."""
    
    SEVERITY_WEIGHTS = {
        "critical": 10,
        "high": 7,
        "medium": 4,
        "low": 1
    }
    
    @staticmethod
    def functional_correctness(generated_code, test_code, timeout=30):
        """Execute generated code + tests, return pass/fail + error details."""
        full_code = generated_code.strip() + "\n\n" + test_code.strip()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(full_code)
            f.flush()
            temp_path = f.name
        
        try:
            result = subprocess.run(
                [sys.executable, temp_path],
                capture_output=True,
                text=True,
                timeout=timeout,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
            )
            passed = result.returncode == 0 and "PASSED" in result.stdout
            error = result.stderr.strip() if result.stderr else result.stdout.strip()
            return {
                "passed": passed,
                "error": error if not passed else None,
                "stdout": result.stdout.strip(),
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"passed": False, "error": "Timeout", "stdout": "", "returncode": -1}
        except Exception as e:
            return {"passed": False, "error": str(e), "stdout": "", "returncode": -1}
        finally:
            os.unlink(temp_path)
    
    @staticmethod
    def domain_keyword_coverage(generated_code, domain_keywords):
        """Measures how many domain-specific keywords/APIs the model used."""
        code_lower = generated_code.lower()
        found = []
        missing = []
        for kw in domain_keywords:
            if kw.lower() in code_lower:
                found.append(kw)
            else:
                missing.append(kw)
        coverage = len(found) / len(domain_keywords) if domain_keywords else 0
        return {
            "coverage": round(coverage, 3),
            "found_keywords": found,
            "missing_keywords": missing
        }
    
    @staticmethod
    def code_quality_analysis(generated_code):
        """Analyzes code quality: structure, documentation, error handling."""
        lines = generated_code.strip().split('\n')
        non_empty = [l for l in lines if l.strip()]
        
        # Documentation
        has_docstring = '"""' in generated_code or "'''" in generated_code
        comment_lines = sum(1 for l in non_empty if l.strip().startswith('#'))
        comment_ratio = comment_lines / len(non_empty) if non_empty else 0
        
        # Error handling
        has_try_except = 'try:' in generated_code and 'except' in generated_code
        has_raise = 'raise ' in generated_code
        has_validation = bool(re.search(r'if\s+not\s|if\s+.*[<>=!]', generated_code))
        
        # Complexity indicators
        n_functions = len(re.findall(r'^\s*def\s+', generated_code, re.MULTILINE))
        n_classes = len(re.findall(r'^\s*class\s+', generated_code, re.MULTILINE))
        max_indent = max((len(l) - len(l.lstrip())) for l in non_empty) if non_empty else 0
        
        # Type hints
        has_type_hints = bool(re.search(r'def\s+\w+\(.*:\s*\w+', generated_code)) or \
                         bool(re.search(r'->\s*\w+', generated_code))
        
        # Import analysis
        imports = re.findall(r'^(?:from\s+\S+\s+)?import\s+.+', generated_code, re.MULTILINE)
        
        quality_score = 0
        max_score = 10
        if has_docstring: quality_score += 2
        if comment_ratio > 0.05: quality_score += 1
        if has_try_except or has_raise: quality_score += 2
        if has_validation: quality_score += 2
        if has_type_hints: quality_score += 1
        if max_indent <= 20: quality_score += 1  # not overly nested
        if len(non_empty) > 0: quality_score += 1
        
        return {
            "quality_score": round(quality_score / max_score, 3),
            "has_docstring": has_docstring,
            "comment_ratio": round(comment_ratio, 3),
            "has_error_handling": has_try_except or has_raise,
            "has_input_validation": has_validation,
            "has_type_hints": has_type_hints,
            "n_functions": n_functions,
            "n_classes": n_classes,
            "n_lines": len(non_empty),
            "max_nesting_depth": max_indent // 4,
            "n_imports": len(imports)
        }
    
    @staticmethod
    def compliance_check(generated_code, compliance_checks, domain):
        """Domain-specific compliance verification."""
        results = {}
        code_lower = generated_code.lower()
        
        check_map = {
            # Healthcare
            "uses_uuid_for_id": lambda c: "uuid" in c,
            "validates_gender_enum": lambda c: any(w in c for w in ["male", "female", "other", "unknown"]) and ("raise" in c or "valid" in c),
            "fhir_compliant_structure": lambda c: "resourcetype" in c and "patient" in c,
            "iso8601_timestamps": lambda c: "isoformat" in c or "iso" in c or "datetime" in c,
            "input_validation": lambda c: "raise" in c or "valueerror" in c or "assert" in c or "if not" in c,
            "clinical_accuracy": lambda c: "bmi" in c or "weight" in c,
            "proper_categorization": lambda c: "underweight" in c and "overweight" in c,
            "case_insensitive_matching": lambda c: ".lower()" in c or "casefold" in c or re.search(r'(?i)case.?insensitive', c) is not None,
            "severity_ordering": lambda c: "minor" in c and "major" in c,
            "comprehensive_pairwise_check": lambda c: "combinations" in c or ("for" in c and "for" in c[c.index("for")+3:]),
            "safety_validation": lambda c: "safe" in c or "max_severity" in c,
            "hl7_structure_parsing": lambda c: "split" in c and ("|" in c or "pipe" in c),
            "component_separation": lambda c: "^" in c or "component" in c,
            "multi_segment_handling": lambda c: ("list" in c or "append" in c) and ("obx" in c or "segment" in c or "existing" in c),
            "whitespace_handling": lambda c: "strip" in c,
            "hipaa_18_identifiers": lambda c: sum(1 for w in ["name", "ssn", "phone", "email", "address", "mrn", "dob", "ip_address"] if w in c) >= 4,
            "recursive_masking": lambda c: "recursive" in c or ("isinstance" in c and "dict" in c) or ("def " in c and c.count("def ") > 0 and "_mask" in c),
            "immutable_input": lambda c: "copy" in c or "deepcopy" in c or "new" in c,
            "date_generalization": lambda c: ("[:4]" in c or "year" in c) and ("dob" in c or "birth" in c or "date" in c),
            
            # Finance
            "correct_var_formula": lambda c: "percentile" in c or "sorted" in c or "quantile" in c,
            "positive_loss_convention": lambda c: "-" in c and ("sorted" in c or "mean" in c),
            "method_selection": lambda c: "historical" in c and "parametric" in c,
            "long_only_constraint": lambda c: ">= 0" in c or ">0" in c or "positive" in c or "sum" in c,
            "weights_sum_to_one": lambda c: "sum" in c and ("1" in c or "one" in c or "1.0" in c),
            "sharpe_ratio_formula": lambda c: "sharpe" in c and ("risk_free" in c or "rf" in c or "risk" in c),
            "dimension_validation": lambda c: "len" in c and ("raise" in c or "assert" in c),
            "correct_bs_formula": lambda c: "d1" in c and "d2" in c and ("log" in c or "ln" in c),
            "put_call_parity": lambda c: "call" in c and "put" in c,
            "greeks_computation": lambda c: "delta" in c,
            "audit_trail": lambda c: "hash" in c or "sha" in c or "audit" in c,
            "hash_integrity": lambda c: "sha256" in c or "hashlib" in c,
            "immutability": lambda c: "__setattr__" in c or "frozen" in c or "immutable" in c or "readonly" in c,
            "iso_timestamp": lambda c: "isoformat" in c or "datetime" in c,
            "gbm_formula": lambda c: "exp" in c and ("sigma" in c or "volatil" in c) and "sqrt" in c,
            "discounting": lambda c: "discount" in c or ("exp" in c and "-r" in c),
            "confidence_interval": lambda c: "1.96" in c or "confidence" in c or "z_score" in c,
            "reproducible_seed": lambda c: "seed" in c,
            "standard_error": lambda c: "std" in c and ("sqrt" in c or "error" in c),
            
            # Molecular
            "smiles_parsing": lambda c: "smiles" in c or ("atom" in c and "bond" in c),
            "atom_recognition": lambda c: any(a in c for a in ["'C'", "'N'", "'O'", "'S'"]),
            "bond_type_detection": lambda c: "single" in c and "double" in c,
            "ring_detection": lambda c: "ring" in c and "digit" in c,
            "formula_computation": lambda c: "formula" in c or "composition" in c,
            "correct_weights": lambda c: "1.008" in c or "12.011" in c or "15.999" in c,
            "formula_parsing": lambda c: "re." in c or "regex" in c or "findall" in c or "match" in c,
            "mass_fraction_calculation": lambda c: "fraction" in c or "/" in c,
            "unknown_element_handling": lambda c: "raise" in c or "unknown" in c or "error" in c,
            "lj_formula": lambda c: ("sigma" in c and "epsilon" in c) and ("12" in c or "6" in c),
            "periodic_boundary": lambda c: "box" in c and ("round" in c or "floor" in c or "int" in c),
            "minimum_image_convention": lambda c: "round" in c and ("box" in c or "period" in c),
            "newtons_third_law": lambda c: "+=" in c and "-=" in c,
            "cutoff_applied": lambda c: "cutoff" in c and ("<" in c or ">" in c),
            "lipinski_thresholds": lambda c: "500" in c and "5" in c and "10" in c,
            "violation_counting": lambda c: "violation" in c and "len" in c,
            "veber_rules": lambda c: "veber" in c or ("rotatable" in c and "psa" in c),
            "score_calculation": lambda c: "score" in c,
            "gradient_descent": lambda c: "gradient" in c or "grad" in c,
            "adaptive_step_size": lambda c: ("step" in c or "alpha" in c or "lr" in c) and ("*" in c or "halv" in c or "0.5" in c or "1.2" in c),
            "convergence_criterion": lambda c: "convergence" in c or "tol" in c or "threshold" in c,
            "energy_decrease": lambda c: "energy" in c and ("<" in c or "decrease" in c or "new" in c),
            
            # Legal
            "clause_extraction": lambda c: "clause" in c and ("re." in c or "split" in c or "findall" in c or "match" in c),
            "party_identification": lambda c: "part" in c and ("between" in c or "v." in c or "extract" in c),
            "date_extraction": lambda c: ("january" in c or "month" in c or r"\d" in c) and ("date" in c or "year" in c),
            "clause_classification": lambda c: "type" in c and any(w in c for w in ["definition", "obligation", "termination"]),
            "citation_format_recognition": lambda c: "case" in c and ("statute" in c or "regulation" in c),
            "party_extraction": lambda c: " v. " in c or "parties" in c or "v\\." in c,
            "volume_reporter_parsing": lambda c: "volume" in c or "reporter" in c,
            "bluebook_compliance": lambda c: "u.s.c" in c or "c.f.r" in c or "u.s." in c,
            "gdpr_article_6_legal_basis": lambda c: "legal_basis" in c and "consent" in c,
            "special_category_handling": lambda c: "special" in c and ("health" in c or "biometric" in c or "genetic" in c),
            "dpia_requirement": lambda c: "dpia" in c,
            "article_30_records": lambda c: "record" in c and ("processing" in c or "purpose" in c),
            "pii_detection": lambda c: "ssn" in c or "phone" in c or "name" in c,
            "redaction_modes": lambda c: "mask" in c and ("remove" in c or "generalize" in c),
            "audit_trail_of_redactions": lambda c: "redaction" in c and ("list" in c or "append" in c),
            "pattern_coverage": lambda c: "re." in c or "pattern" in c or "regex" in c,
            "pattern_matching": lambda c: "re." in c or "pattern" in c or "findall" in c,
            "risk_scoring": lambda c: "score" in c and "severity" in c,
            "document_comparison": lambda c: "compare" in c or ("doc1" in c and "doc2" in c),
            "report_generation": lambda c: "report" in c and ("join" in c or "format" in c or "f'" in c),
        }
        
        passed = 0
        total = len(compliance_checks)
        for check in compliance_checks:
            if check in check_map:
                try:
                    result = check_map[check](code_lower)
                    results[check] = result
                    if result:
                        passed += 1
                except:
                    results[check] = False
            else:
                results[check] = "unknown_check"
        
        return {
            "compliance_score": round(passed / total, 3) if total > 0 else 0,
            "checks_passed": passed,
            "checks_total": total,
            "details": results
        }
    
    @staticmethod
    def code_similarity(generated_code, reference_solution):
        """Simple structural similarity between generated and reference code."""
        def tokenize(code):
            tokens = re.findall(r'\b\w+\b', code.lower())
            return set(tokens)
        
        gen_tokens = tokenize(generated_code)
        ref_tokens = tokenize(reference_solution)
        
        if not gen_tokens or not ref_tokens:
            return {"similarity": 0.0}
        
        intersection = gen_tokens & ref_tokens
        union = gen_tokens | ref_tokens
        jaccard = len(intersection) / len(union) if union else 0
        
        # Also check structural patterns
        gen_patterns = set(re.findall(r'(def\s+\w+|class\s+\w+|import\s+\w+|from\s+\w+)', generated_code))
        ref_patterns = set(re.findall(r'(def\s+\w+|class\s+\w+|import\s+\w+|from\s+\w+)', reference_solution))
        
        pattern_overlap = len(gen_patterns & ref_patterns) / len(ref_patterns) if ref_patterns else 0
        
        return {
            "jaccard_similarity": round(jaccard, 3),
            "structural_similarity": round(pattern_overlap, 3),
            "combined_similarity": round((jaccard + pattern_overlap) / 2, 3)
        }


# ============================================================
# EVALUATION ENGINE
# ============================================================

class EvaluationEngine:
    """Main engine that runs evaluations across models and tasks."""
    
    def __init__(self, prompts, models_config):
        self.prompts = prompts
        self.models_config = models_config
        self.metrics = DomainMetrics()
        self.results = {}
    
    def generate_code(self, model_id, prompt_text, tokenizer, model, max_new_tokens=2048):
        """Generate code from a model given a prompt."""
        system_msg = (
            "You are an expert software engineer. Write clean, correct, production-quality Python code. "
            "Return ONLY the code, no explanations or markdown formatting. "
            "Do not wrap the code in ```python blocks."
        )
        
        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": prompt_text}
        ]
        
        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = tokenizer([text], return_tensors="pt").to(model.device)
        
        with __import__('torch').no_grad():
            output_ids = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=0.1,
                top_p=0.95,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )
        
        response = tokenizer.decode(
            output_ids[0][len(inputs.input_ids[0]):], 
            skip_special_tokens=True
        )
        
        # Clean up response - extract code
        response = self._extract_code(response)
        return response
    
    def _extract_code(self, response):
        """Extract Python code from model response, handling markdown blocks."""
        # Try to extract from markdown code blocks
        code_blocks = re.findall(r'```(?:python)?\n(.*?)```', response, re.DOTALL)
        if code_blocks:
            return code_blocks[0].strip()
        
        # If the response starts with import/def/class, it's likely pure code
        lines = response.strip().split('\n')
        code_lines = []
        in_code = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith(('import ', 'from ', 'def ', 'class ', '#', '@')) or in_code:
                code_lines.append(line)
                in_code = True
            elif in_code and (line.startswith(' ') or line.startswith('\t') or stripped == ''):
                code_lines.append(line)
            elif not in_code and stripped:
                # Skip non-code preamble
                continue
        
        if code_lines:
            return '\n'.join(code_lines).strip()
        
        return response.strip()
    
    def evaluate_single(self, model_name, generated_code, task):
        """Run all evaluation metrics on a single generated code."""
        result = {
            "task_id": task["task_id"],
            "domain": task["domain"],
            "subdomain": task["subdomain"],
            "difficulty": task["difficulty"],
            "model": model_name,
            "generated_code": generated_code,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # 1. Functional correctness
        result["functional"] = self.metrics.functional_correctness(
            generated_code, task["test_code"]
        )
        
        # 2. Domain keyword coverage
        result["domain_coverage"] = self.metrics.domain_keyword_coverage(
            generated_code, task["domain_keywords"]
        )
        
        # 3. Code quality
        result["code_quality"] = self.metrics.code_quality_analysis(generated_code)
        
        # 4. Compliance checks
        result["compliance"] = self.metrics.compliance_check(
            generated_code, task["compliance_checks"], task["domain"]
        )
        
        # 5. Similarity to reference
        result["similarity"] = self.metrics.code_similarity(
            generated_code, task["reference_solution"]
        )
        
        # 6. Composite score
        weights = {
            "functional": 0.40,
            "domain_coverage": 0.15,
            "code_quality": 0.15,
            "compliance": 0.20,
            "similarity": 0.10
        }
        
        composite = (
            weights["functional"] * (1.0 if result["functional"]["passed"] else 0.0) +
            weights["domain_coverage"] * result["domain_coverage"]["coverage"] +
            weights["code_quality"] * result["code_quality"]["quality_score"] +
            weights["compliance"] * result["compliance"]["compliance_score"] +
            weights["similarity"] * result["similarity"]["combined_similarity"]
        )
        result["composite_score"] = round(composite, 4)
        
        return result
    
    def evaluate_model(self, model_name, generated_codes):
        """Evaluate all generated codes for a model."""
        model_results = []
        for task, code in zip(self.prompts, generated_codes):
            result = self.evaluate_single(model_name, code, task)
            model_results.append(result)
        
        self.results[model_name] = model_results
        return model_results
    
    def generate_leaderboard(self):
        """Generate comprehensive leaderboard from all results."""
        leaderboard = {}
        
        for model_name, results in self.results.items():
            # Overall metrics
            n_tasks = len(results)
            pass_rate = sum(1 for r in results if r["functional"]["passed"]) / n_tasks
            avg_composite = sum(r["composite_score"] for r in results) / n_tasks
            avg_domain_cov = sum(r["domain_coverage"]["coverage"] for r in results) / n_tasks
            avg_quality = sum(r["code_quality"]["quality_score"] for r in results) / n_tasks
            avg_compliance = sum(r["compliance"]["compliance_score"] for r in results) / n_tasks
            
            # Per-domain metrics
            domain_metrics = {}
            for domain in ["healthcare", "finance", "molecular_sim", "legal"]:
                domain_results = [r for r in results if r["domain"] == domain]
                if domain_results:
                    domain_metrics[domain] = {
                        "pass_rate": round(sum(1 for r in domain_results if r["functional"]["passed"]) / len(domain_results), 3),
                        "avg_composite": round(sum(r["composite_score"] for r in domain_results) / len(domain_results), 4),
                        "avg_domain_coverage": round(sum(r["domain_coverage"]["coverage"] for r in domain_results) / len(domain_results), 3),
                        "avg_compliance": round(sum(r["compliance"]["compliance_score"] for r in domain_results) / len(domain_results), 3),
                        "n_tasks": len(domain_results)
                    }
            
            # Per-difficulty metrics
            difficulty_metrics = {}
            for diff in ["easy", "medium", "hard"]:
                diff_results = [r for r in results if r["difficulty"] == diff]
                if diff_results:
                    difficulty_metrics[diff] = {
                        "pass_rate": round(sum(1 for r in diff_results if r["functional"]["passed"]) / len(diff_results), 3),
                        "avg_composite": round(sum(r["composite_score"] for r in diff_results) / len(diff_results), 4),
                        "n_tasks": len(diff_results)
                    }
            
            leaderboard[model_name] = {
                "overall": {
                    "pass_rate": round(pass_rate, 3),
                    "avg_composite_score": round(avg_composite, 4),
                    "avg_domain_coverage": round(avg_domain_cov, 3),
                    "avg_code_quality": round(avg_quality, 3),
                    "avg_compliance": round(avg_compliance, 3),
                    "n_tasks": n_tasks
                },
                "by_domain": domain_metrics,
                "by_difficulty": difficulty_metrics
            }
        
        return leaderboard
    
    def generate_report(self, leaderboard):
        """Generate a detailed markdown report."""
        report = []
        report.append("# 🏆 Domain-Specific Code Generation Benchmark Results\n")
        report.append(f"**Evaluation Date:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n")
        report.append(f"**Total Tasks:** {len(self.prompts)} across 4 domains\n")
        report.append(f"**Models Evaluated:** {len(self.results)}\n")
        
        # Domains
        report.append("**Domains:**\n")
        report.append("- 🏥 Healthcare Systems (FHIR, HL7, HIPAA, Clinical)\n")
        report.append("- 💰 Financial Algorithms (VaR, Black-Scholes, Monte Carlo, Portfolio)\n")  
        report.append("- 🧬 Molecular Simulation (SMILES, Force Fields, Drug-Likeness)\n")
        report.append("- ⚖️ Legal Processing (Contracts, Citations, GDPR, Redaction)\n\n")
        
        # Evaluation metrics
        report.append("## 📊 Evaluation Metrics\n")
        report.append("| Metric | Weight | Description |\n")
        report.append("|--------|--------|-------------|\n")
        report.append("| Functional Correctness | 40% | Code passes all test cases |\n")
        report.append("| Compliance Score | 20% | Meets domain-specific standards |\n")
        report.append("| Domain Coverage | 15% | Uses appropriate domain APIs/terms |\n")
        report.append("| Code Quality | 15% | Documentation, error handling, structure |\n")
        report.append("| Reference Similarity | 10% | Structural match to expert solution |\n\n")
        
        # Overall leaderboard
        report.append("## 🏆 Overall Leaderboard\n\n")
        sorted_models = sorted(
            leaderboard.items(), 
            key=lambda x: x[1]["overall"]["avg_composite_score"], 
            reverse=True
        )
        
        report.append("| Rank | Model | Composite Score | Pass Rate | Domain Cov. | Quality | Compliance |\n")
        report.append("|------|-------|----------------|-----------|-------------|---------|------------|\n")
        
        for rank, (model, data) in enumerate(sorted_models, 1):
            o = data["overall"]
            medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"{rank}."
            short_name = model.split("/")[-1] if "/" in model else model
            report.append(
                f"| {medal} | {short_name} | {o['avg_composite_score']:.4f} | "
                f"{o['pass_rate']:.1%} | {o['avg_domain_coverage']:.1%} | "
                f"{o['avg_code_quality']:.1%} | {o['avg_compliance']:.1%} |\n"
            )
        
        # Per-domain analysis
        report.append("\n## 📈 Domain-Specific Analysis\n")
        
        domain_names = {
            "healthcare": "🏥 Healthcare Systems",
            "finance": "💰 Financial Algorithms",
            "molecular_sim": "🧬 Molecular Simulation",
            "legal": "⚖️ Legal Processing"
        }
        
        for domain, domain_label in domain_names.items():
            report.append(f"\n### {domain_label}\n\n")
            report.append("| Model | Pass Rate | Composite | Domain Cov. | Compliance |\n")
            report.append("|-------|-----------|-----------|-------------|------------|\n")
            
            domain_ranked = sorted(
                [(m, d["by_domain"].get(domain, {})) for m, d in leaderboard.items()],
                key=lambda x: x[1].get("avg_composite", 0),
                reverse=True
            )
            
            for model, ddata in domain_ranked:
                if ddata:
                    short_name = model.split("/")[-1] if "/" in model else model
                    report.append(
                        f"| {short_name} | {ddata.get('pass_rate', 0):.1%} | "
                        f"{ddata.get('avg_composite', 0):.4f} | "
                        f"{ddata.get('avg_domain_coverage', 0):.1%} | "
                        f"{ddata.get('avg_compliance', 0):.1%} |\n"
                    )
        
        # Difficulty analysis
        report.append("\n## 📉 Performance by Difficulty\n\n")
        report.append("| Model | Easy Pass% | Medium Pass% | Hard Pass% |\n")
        report.append("|-------|-----------|-------------|------------|\n")
        
        for model, data in sorted_models:
            short_name = model.split("/")[-1] if "/" in model else model
            easy = data["by_difficulty"].get("easy", {}).get("pass_rate", 0)
            medium = data["by_difficulty"].get("medium", {}).get("pass_rate", 0)
            hard = data["by_difficulty"].get("hard", {}).get("pass_rate", 0)
            report.append(f"| {short_name} | {easy:.1%} | {medium:.1%} | {hard:.1%} |\n")
        
        # Key findings
        report.append("\n## 🔍 Key Findings\n\n")
        
        if sorted_models:
            best_model = sorted_models[0][0].split("/")[-1]
            report.append(f"1. **Overall Winner:** {best_model} leads in composite score\n")
            
            # Best per domain
            for domain, domain_label in domain_names.items():
                best_in_domain = max(
                    [(m, d["by_domain"].get(domain, {}).get("avg_composite", 0)) 
                     for m, d in leaderboard.items()],
                    key=lambda x: x[1]
                )
                short = best_in_domain[0].split("/")[-1]
                report.append(f"2. **Best in {domain_label}:** {short} (composite: {best_in_domain[1]:.4f})\n")
        
        # Methodology
        report.append("\n## 📋 Methodology\n\n")
        report.append("### Benchmark Design\n")
        report.append("- **20 tasks** across 4 specialized domains (5 per domain)\n")
        report.append("- Each task includes: natural language prompt, test suite, reference solution\n")
        report.append("- Difficulty levels: Easy (2), Medium (10), Hard (8)\n")
        report.append("- Domain-specific compliance checks per task\n\n")
        
        report.append("### Evaluation Protocol\n")
        report.append("- Temperature: 0.1 (near-deterministic)\n")
        report.append("- Max new tokens: 2048\n")
        report.append("- Single attempt per task (no retries)\n")
        report.append("- Automated test execution with 30s timeout\n")
        report.append("- 5 evaluation dimensions with weighted composite score\n\n")
        
        report.append("### Domain-Specific Quality Criteria\n")
        report.append("- **Healthcare:** FHIR compliance, HIPAA de-identification, clinical accuracy, HL7 parsing\n")
        report.append("- **Finance:** Mathematical correctness (Black-Scholes, VaR), audit trails, risk management\n")
        report.append("- **Molecular:** Physical accuracy (Lennard-Jones), SMILES parsing, Lipinski rules, energy minimization\n")
        report.append("- **Legal:** Contract clause extraction, citation parsing (Bluebook), GDPR compliance, document redaction\n\n")
        
        report.append("## 📄 Citation\n\n")
        report.append("```bibtex\n")
        report.append("@misc{domain_code_bench_2024,\n")
        report.append("  title={Domain-Specific Code Generation Benchmark},\n")
        report.append("  author={DomainCodeBench Team},\n")
        report.append("  year={2024},\n")
        report.append("  howpublished={\\url{https://huggingface.co/datasets/umaimakhan01/domain-code-bench}}\n")
        report.append("}\n")
        report.append("```\n")
        
        return "".join(report)


if __name__ == "__main__":
    from benchmark_prompts import BENCHMARK_PROMPTS
    
    engine = EvaluationEngine(BENCHMARK_PROMPTS, {})
    
    # Test with reference solutions
    print("Testing evaluation framework with reference solutions...")
    ref_results = []
    for task in BENCHMARK_PROMPTS:
        result = engine.evaluate_single("reference", task["reference_solution"], task)
        ref_results.append(result)
        status = "✅" if result["functional"]["passed"] else "❌"
        print(f"  {status} {task['task_id']}: composite={result['composite_score']:.3f}, "
              f"domain_cov={result['domain_coverage']['coverage']:.2f}, "
              f"compliance={result['compliance']['compliance_score']:.2f}")
    
    engine.results["reference"] = ref_results
    
    passed = sum(1 for r in ref_results if r["functional"]["passed"])
    print(f"\nReference solutions: {passed}/{len(ref_results)} passed")
    print(f"Avg composite: {sum(r['composite_score'] for r in ref_results)/len(ref_results):.4f}")
