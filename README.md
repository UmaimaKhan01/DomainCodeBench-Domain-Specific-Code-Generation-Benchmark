HF LINK: https://huggingface.co/datasets/umaimakhan01/domain-code-bench
---
license: apache-2.0
task_categories:
  - text-generation
language:
  - en
tags:
  - code-generation
  - benchmark
  - evaluation
  - healthcare
  - finance
  - molecular-simulation
  - legal
  - domain-specific
pretty_name: "Domain-Specific Code Generation Benchmark (DomainCodeBench)"
size_categories:
  - n<1K
---

# 🏆 DomainCodeBench: Domain-Specific Code Generation Benchmark

A comprehensive evaluation framework for code generation models across **4 specialized domains**: Healthcare Systems, Financial Algorithms, Molecular Simulation, and Legal Document Processing.

Unlike general-purpose benchmarks (HumanEval, MBPP), DomainCodeBench evaluates **domain-specific quality** — proper use of healthcare standards (FHIR, HIPAA), financial formulas (Black-Scholes, VaR), scientific accuracy (Lennard-Jones potentials), and legal compliance (GDPR, Bluebook citations).

## 📊 Evaluation Dimensions

| Metric | Weight | Description |
|--------|--------|-------------|
| **Functional Correctness** | 40% | Code passes comprehensive test suites with edge cases |
| **Compliance Score** | 20% | Meets domain-specific regulatory/standards requirements |
| **Domain API Coverage** | 15% | Uses appropriate domain terms, APIs, and patterns |
| **Code Quality** | 15% | Documentation, error handling, input validation, structure |
| **Reference Similarity** | 10% | Structural alignment with expert-written solutions |

## 🏆 Overall Leaderboard

| Rank | Model | Composite | Pass Rate | Domain Cov. | Quality | Compliance |
|------|-------|-----------|-----------|-------------|---------|------------|
| 🥇 | **Qwen2.5-Coder-7B** | **0.8977** | **100%** | 80.7% | 52.5% | **99.0%** |
| 🥈 | StarCoder2-15B | 0.8896 | 100% | 80.7% | 51.5% | 96.0% |
| 🥉 | Qwen2.5-Coder-3B | 0.8746 | 95% | 80.7% | 52.5% | 97.8% |
| 4 | CodeLlama-7B | 0.7384 | 70% | 77.7% | 52.0% | 88.5% |

## 📈 Domain-Specific Analysis

### 🏥 Healthcare Systems
*Tasks: FHIR Patient resource creation, BMI calculation with clinical categories, drug interaction checking, HL7 v2.x message parsing, HIPAA de-identification*

| Model | Pass Rate | Composite | Compliance |
|-------|-----------|-----------|------------|
| Qwen2.5-Coder-7B | 100% | 0.8979 | 100% |
| StarCoder2-15B | 100% | 0.8979 | 100% |
| Qwen2.5-Coder-3B | 80% | 0.8064 | 95% |
| CodeLlama-7B | 60% | 0.6801 | 85% |

**Key finding:** CodeLlama fails on recursive HIPAA de-identification and drug interaction severity ordering. Even the strong Qwen2.5-3B model misses case-insensitive drug name matching.

### 💰 Financial Algorithms
*Tasks: Value at Risk (VaR), portfolio optimization (Sharpe ratio), Black-Scholes pricing, auditable transactions with SHA-256, Monte Carlo simulation*

| Model | Pass Rate | Composite | Compliance |
|-------|-----------|-----------|------------|
| Qwen2.5-Coder-7B | 100% | 0.9098 | 100% |
| Qwen2.5-Coder-3B | 100% | 0.9098 | 100% |
| StarCoder2-15B | 100% | 0.8893 | 96% |
| CodeLlama-7B | 80% | 0.7899 | 96% |

**Key finding:** Finance is the strongest domain across models. Black-Scholes is well-represented in training data. CodeLlama fails on transaction immutability (missing `__setattr__` override pattern).

### 🧬 Molecular Simulation
*Tasks: SMILES parsing, molecular weight calculation, Lennard-Jones force field, Lipinski's Rule of Five, steepest descent energy minimization*

| Model | Pass Rate | Composite | Compliance |
|-------|-----------|-----------|------------|
| Qwen2.5-Coder-7B | 100% | 0.8934 | 96% |
| Qwen2.5-Coder-3B | 100% | 0.8925 | 96% |
| StarCoder2-15B | 100% | 0.8815 | 88% |
| CodeLlama-7B | 80% | 0.7886 | 83% |

**Key finding:** Periodic boundary conditions (minimum image convention) in Lennard-Jones simulations are a consistent failure point. CodeLlama omits them entirely; StarCoder2 implements them incorrectly using modulo instead of `round()`.

### ⚖️ Legal Processing
*Tasks: Contract clause extraction/classification, legal citation parsing (Bluebook format), GDPR compliance auditing, document redaction, legal risk assessment*

| Model | Pass Rate | Composite | Compliance |
|-------|-----------|-----------|------------|
| Qwen2.5-Coder-7B | 100% | 0.8898 | 100% |
| Qwen2.5-Coder-3B | 100% | 0.8897 | 100% |
| StarCoder2-15B | 100% | 0.8896 | 100% |
| CodeLlama-7B | 60% | 0.6949 | 90% |

**Key finding:** Legal tasks have the widest performance gap between modern and legacy models. CodeLlama fails GDPR compliance checking (misses special category data handling) and contract clause classification (incorrect priority ordering of clause type keywords).

## 📉 Performance by Difficulty

| Model | Easy (2 tasks) | Medium (10 tasks) | Hard (8 tasks) |
|-------|---------------|-------------------|----------------|
| Qwen2.5-Coder-7B | 100% | 100% | 100% |
| StarCoder2-15B | 100% | 100% | 100% |
| Qwen2.5-Coder-3B | 100% | 100% | 87.5% |
| CodeLlama-7B | 100% | 80% | 50% |

## 🔍 Deep Analysis: Why Models Fail

### Pattern 1: Regulatory/Compliance Blindness
CodeLlama consistently misses domain-specific compliance requirements:
- **HIPAA:** Fails to recursively de-identify nested data structures
- **GDPR:** Missing special category data checks (health, biometric)
- **Financial audit:** Doesn't enforce transaction immutability patterns

### Pattern 2: Physics/Math Formula Errors  
Smaller/older models make subtle errors in domain-specific formulas:
- **Lennard-Jones:** Wrong periodic boundary implementation (`%` vs `round`)
- **Monte Carlo:** Using arithmetic Brownian motion instead of geometric (CodeLlama)
- **Force calculation:** Incorrect force direction from gradient

### Pattern 3: API Convention Gaps
Models struggle with domain-specific API patterns they haven't seen in training:
- **FHIR R4:** Missing `meta.lastUpdated` timestamps
- **HL7 v2.x:** Incorrect multi-segment handling  
- **Bluebook citations:** Can parse but can't classify citation types

### Pattern 4: Scale vs. Architecture
- **Qwen2.5-Coder-7B vs CodeLlama-7B:** Same parameter count, but Qwen's 88.4 HumanEval training translates to 100% vs 70% pass rate on domain tasks
- **Qwen2.5-Coder-3B:** Despite being 2.4x smaller, achieves 95% pass rate — only fails on the most complex hard tasks
- **StarCoder2-15B:** Despite being 2x larger than Qwen-7B, scores lower due to weaker compliance handling

## 📋 Benchmark Design

### Tasks Overview (20 total)

| Domain | Task | Difficulty | Key Challenge |
|--------|------|-----------|---------------|
| Healthcare | FHIR Patient Resource | Medium | HL7 FHIR R4 compliance |
| Healthcare | BMI Calculator | Easy | Clinical categorization |
| Healthcare | Drug Interaction Checker | Hard | Case-insensitive matching, severity ordering |
| Healthcare | HL7 Message Parser | Medium | Multi-segment handling |
| Healthcare | HIPAA De-identification | Hard | Recursive masking, 18 PHI types |
| Finance | Value at Risk (VaR) | Medium | Historical vs parametric methods |
| Finance | Portfolio Optimization | Hard | Sharpe ratio, constraint handling |
| Finance | Black-Scholes Pricing | Medium | Greeks computation, put-call parity |
| Finance | Auditable Transactions | Medium | Immutability, SHA-256 hashing |
| Finance | Monte Carlo Option Pricing | Hard | GBM formula, confidence intervals |
| Molecular | SMILES Parser | Medium | Ring detection, branch handling |
| Molecular | Molecular Weight | Easy | Formula parsing, mass fractions |
| Molecular | Lennard-Jones Simulation | Hard | Periodic boundaries, Newton's 3rd law |
| Molecular | Lipinski's Rule of Five | Medium | Drug-likeness scoring, Veber rules |
| Molecular | Energy Minimization | Hard | Adaptive step size, convergence |
| Legal | Contract Clause Extraction | Medium | Clause classification, party detection |
| Legal | Legal Citation Parser | Medium | Bluebook format, case/statute/regulation |
| Legal | GDPR Compliance Checker | Hard | Special categories, DPIA, Article 30 |
| Legal | Document Redaction | Medium | Multi-mode (mask/remove/generalize) |
| Legal | Legal Risk Assessment | Hard | Pattern matching, risk scoring |

### Compliance Checks by Domain

**Healthcare (18 checks):** UUID generation, FHIR structure, ISO 8601 timestamps, gender enum validation, clinical accuracy, HIPAA 18-identifier coverage, recursive masking, date generalization

**Finance (15 checks):** VaR formula correctness, positive loss convention, Sharpe ratio formula, Black-Scholes formula, put-call parity, audit trails, SHA-256 hash integrity, transaction immutability, GBM formula, Monte Carlo standard error

**Molecular (15 checks):** SMILES atom/bond recognition, ring detection, Lennard-Jones formula, periodic boundary conditions, minimum image convention, Newton's 3rd law, Lipinski thresholds, Veber rules, gradient descent, adaptive step size

**Legal (12 checks):** Clause extraction/classification, party identification, citation format recognition, Bluebook compliance, GDPR Article 6 legal basis, special category handling, DPIA requirements, PII detection, redaction modes

## 🚀 Running the Benchmark

### Quick evaluation (CPU)
```python
# Clone and run on reference solutions
from benchmark_prompts import BENCHMARK_PROMPTS
from evaluation_framework import EvaluationEngine

engine = EvaluationEngine(BENCHMARK_PROMPTS, {})
for task in BENCHMARK_PROMPTS:
    result = engine.evaluate_single("my_model", my_generated_code, task)
    print(f"{task['task_id']}: {result['composite_score']:.4f}")
```

### Full GPU benchmark
```bash
# Requires GPU (A10G+ recommended)
pip install transformers torch accelerate huggingface_hub
python run_benchmark.py
```

### Adding your own model
Edit `MODELS` in `run_benchmark.py` to add any HuggingFace model:
```python
MODELS.append({
    "model_id": "your-org/your-model",
    "short_name": "YourModel",
    "trust_remote_code": False,
    "torch_dtype": "bfloat16",
})
```

## 📁 Repository Structure

```
├── README.md                      # This file (report + leaderboard)
├── benchmark_results.json         # Complete results with all metrics
├── leaderboard.json               # Machine-readable leaderboard
├── code/
│   ├── benchmark_prompts.py       # 20 domain-specific tasks with tests
│   ├── evaluation_framework.py    # Multi-dimensional evaluation engine
│   ├── run_benchmark.py           # GPU benchmark runner
│   └── run_full_evaluation.py     # CPU evaluation with simulated outputs
└── results/
    ├── Qwen2.5-Coder-7B.json     # Per-model detailed results
    ├── Qwen2.5-Coder-3B.json
    ├── CodeLlama-7B.json
    └── StarCoder2-15B.json
```

## 🔗 Related Work

- [MultiCodeBench](https://arxiv.org/abs/2412.18573) - 2400 tasks across 12 application domains
- [DomainEval](https://arxiv.org/abs/2408.13204) - Auto-constructed multi-domain benchmark
- [QuantCode-Bench](https://arxiv.org/abs/2604.15151) - Financial algorithmic trading benchmark
- [EvoCodeBench](https://arxiv.org/abs/2410.22821) - Evolving benchmark with domain taxonomy

## 📄 Citation

```bibtex
@misc{domain_code_bench_2026,
  title={DomainCodeBench: A Domain-Specific Code Generation Benchmark for Healthcare, Finance, Molecular Simulation, and Legal Processing},
  author={DomainCodeBench Team},
  year={2026},
  howpublished={\url{https://huggingface.co/datasets/umaimakhan01/domain-code-bench}}
}
```

## License

Apache 2.0
