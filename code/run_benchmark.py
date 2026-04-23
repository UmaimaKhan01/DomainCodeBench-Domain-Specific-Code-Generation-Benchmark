"""
Domain-Specific Code Generation Benchmark Runner
=================================================
Runs evaluation across multiple code generation models.
Designed to run on GPU infrastructure (A10G/A100).

Models evaluated:
1. Qwen/Qwen2.5-Coder-7B-Instruct (SOTA 7B)
2. Qwen/Qwen2.5-Coder-3B-Instruct (Small model)
3. codellama/CodeLlama-7b-Instruct-hf (Legacy baseline)
4. bigcode/starcoder2-15b-instruct-v0.1 (Self-aligned)
"""

import json
import os
import sys
import time
import gc
import traceback
from datetime import datetime, timezone

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from huggingface_hub import HfApi, login

# ============================================================
# Configuration
# ============================================================

MODELS = [
    {
        "model_id": "Qwen/Qwen2.5-Coder-7B-Instruct",
        "short_name": "Qwen2.5-Coder-7B",
        "trust_remote_code": False,
        "torch_dtype": "bfloat16",
    },
    {
        "model_id": "Qwen/Qwen2.5-Coder-3B-Instruct",
        "short_name": "Qwen2.5-Coder-3B",
        "trust_remote_code": False,
        "torch_dtype": "bfloat16",
    },
    {
        "model_id": "codellama/CodeLlama-7b-Instruct-hf",
        "short_name": "CodeLlama-7B",
        "trust_remote_code": False,
        "torch_dtype": "bfloat16",
    },
    {
        "model_id": "bigcode/starcoder2-15b-instruct-v0.1",
        "short_name": "StarCoder2-15B",
        "trust_remote_code": False,
        "torch_dtype": "bfloat16",
    },
]

OUTPUT_REPO = "umaimakhan01/domain-code-bench"
MAX_NEW_TOKENS = 2048
TEMPERATURE = 0.1
TOP_P = 0.95

# ============================================================
# Benchmark Prompts (embedded)
# ============================================================

# Import from our module
sys.path.insert(0, '/app')
from benchmark_prompts import BENCHMARK_PROMPTS
from evaluation_framework import EvaluationEngine, DomainMetrics

# ============================================================
# Code Generation
# ============================================================

def generate_code_for_model(model_id, tokenizer, model, prompt_text):
    """Generate code from a model given a prompt."""
    system_msg = (
        "You are an expert software engineer. Write clean, correct, production-quality Python code. "
        "Return ONLY the Python code, no explanations, no markdown formatting, no ```python blocks. "
        "Start directly with imports or function/class definitions."
    )
    
    # Handle different chat templates
    if "codellama" in model_id.lower():
        # CodeLlama uses a specific format
        full_prompt = f"[INST] <<SYS>>\n{system_msg}\n<</SYS>>\n\n{prompt_text} [/INST]"
        inputs = tokenizer(full_prompt, return_tensors="pt").to(model.device)
    elif "starcoder" in model_id.lower():
        # StarCoder2 instruction format
        full_prompt = f"### Instruction\n{system_msg}\n\n{prompt_text}\n\n### Response\n"
        inputs = tokenizer(full_prompt, return_tensors="pt").to(model.device)
    else:
        # Standard chat template (Qwen, etc.)
        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": prompt_text}
        ]
        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = tokenizer([text], return_tensors="pt").to(model.device)
    
    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=MAX_NEW_TOKENS,
            temperature=TEMPERATURE,
            top_p=TOP_P,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )
    
    response = tokenizer.decode(
        output_ids[0][len(inputs.input_ids[0]):],
        skip_special_tokens=True
    )
    
    return extract_code(response)


def extract_code(response):
    """Extract Python code from model response."""
    import re
    
    # Try markdown code blocks first
    code_blocks = re.findall(r'```(?:python)?\n(.*?)```', response, re.DOTALL)
    if code_blocks:
        return code_blocks[0].strip()
    
    # Look for code starting patterns
    lines = response.strip().split('\n')
    code_lines = []
    in_code = False
    
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(('import ', 'from ', 'def ', 'class ', '#', '@', 'BENCHMARK', 'SEVERITY')):
            in_code = True
        
        if in_code:
            code_lines.append(line)
        elif not stripped or stripped.startswith(('Here', 'This', 'The ', 'Below', 'I ')):
            continue
        else:
            # Could be code without standard start
            if any(c in stripped for c in ['=', '(', 'if ', 'for ', 'while ', 'return ']):
                in_code = True
                code_lines.append(line)
    
    if code_lines:
        return '\n'.join(code_lines).strip()
    
    return response.strip()


# ============================================================
# Main Runner
# ============================================================

def run_benchmark():
    """Run the complete benchmark."""
    token = os.environ.get("HF_TOKEN")
    if token:
        login(token=token)
    
    api = HfApi()
    
    # Create output repo if needed
    try:
        api.create_repo(OUTPUT_REPO, repo_type="dataset", exist_ok=True)
        print(f"Output repo ready: {OUTPUT_REPO}")
    except Exception as e:
        print(f"Repo creation note: {e}")
    
    all_results = {}
    all_raw_outputs = {}
    
    print(f"\n{'='*60}")
    print(f"DOMAIN-SPECIFIC CODE GENERATION BENCHMARK")
    print(f"{'='*60}")
    print(f"Models: {len(MODELS)}")
    print(f"Tasks: {len(BENCHMARK_PROMPTS)}")
    print(f"GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}")
    print(f"{'='*60}\n")
    
    engine = EvaluationEngine(BENCHMARK_PROMPTS, {})
    
    for model_config in MODELS:
        model_id = model_config["model_id"]
        short_name = model_config["short_name"]
        
        print(f"\n{'='*60}")
        print(f"Loading model: {model_id}")
        print(f"{'='*60}")
        
        try:
            dtype = getattr(torch, model_config["torch_dtype"])
            
            tokenizer = AutoTokenizer.from_pretrained(
                model_id,
                trust_remote_code=model_config.get("trust_remote_code", False),
                padding_side="left"
            )
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token
            
            model = AutoModelForCausalLM.from_pretrained(
                model_id,
                torch_dtype=dtype,
                device_map="auto",
                trust_remote_code=model_config.get("trust_remote_code", False),
            )
            model.eval()
            
            print(f"Model loaded. Parameters: {sum(p.numel() for p in model.parameters()):,}")
            print(f"Device: {next(model.parameters()).device}")
            
        except Exception as e:
            print(f"ERROR loading {model_id}: {e}")
            traceback.print_exc()
            continue
        
        generated_codes = []
        model_raw = []
        
        for task_idx, task in enumerate(BENCHMARK_PROMPTS):
            print(f"\n  [{task_idx+1}/{len(BENCHMARK_PROMPTS)}] {task['task_id']} ({task['domain']}/{task['subdomain']}) ...", end=" ", flush=True)
            
            start = time.time()
            try:
                code = generate_code_for_model(model_id, tokenizer, model, task["prompt"])
                elapsed = time.time() - start
                print(f"generated in {elapsed:.1f}s ({len(code)} chars)")
                
                generated_codes.append(code)
                model_raw.append({
                    "task_id": task["task_id"],
                    "generated_code": code,
                    "generation_time": elapsed
                })
                
            except Exception as e:
                print(f"ERROR: {e}")
                generated_codes.append(f"# Generation failed: {e}")
                model_raw.append({
                    "task_id": task["task_id"],
                    "generated_code": f"# Generation failed: {e}",
                    "generation_time": 0,
                    "error": str(e)
                })
        
        # Evaluate all generated codes
        print(f"\n  Evaluating {short_name}...")
        results = engine.evaluate_model(short_name, generated_codes)
        
        passed = sum(1 for r in results if r["functional"]["passed"])
        avg_score = sum(r["composite_score"] for r in results) / len(results)
        print(f"  Results: {passed}/{len(results)} passed, avg composite: {avg_score:.4f}")
        
        all_results[short_name] = results
        all_raw_outputs[short_name] = model_raw
        
        # Free memory
        del model
        del tokenizer
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        print(f"  Memory freed.")
    
    # Generate leaderboard
    print(f"\n{'='*60}")
    print("GENERATING LEADERBOARD")
    print(f"{'='*60}")
    
    leaderboard = engine.generate_leaderboard()
    report = engine.generate_report(leaderboard)
    
    # Print summary
    print("\n" + "="*60)
    print("FINAL LEADERBOARD")
    print("="*60)
    sorted_models = sorted(
        leaderboard.items(),
        key=lambda x: x[1]["overall"]["avg_composite_score"],
        reverse=True
    )
    for rank, (model_name, data) in enumerate(sorted_models, 1):
        o = data["overall"]
        print(f"  #{rank} {model_name}: composite={o['avg_composite_score']:.4f}, "
              f"pass_rate={o['pass_rate']:.1%}, compliance={o['avg_compliance']:.1%}")
        for domain, dd in data["by_domain"].items():
            print(f"       {domain}: pass={dd['pass_rate']:.1%}, composite={dd['avg_composite']:.4f}")
    
    # Save all results
    output = {
        "metadata": {
            "benchmark_name": "Domain-Specific Code Generation Benchmark",
            "version": "1.0",
            "date": datetime.now(timezone.utc).isoformat(),
            "n_tasks": len(BENCHMARK_PROMPTS),
            "n_models": len(all_results),
            "domains": ["healthcare", "finance", "molecular_sim", "legal"],
            "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU",
        },
        "leaderboard": leaderboard,
        "detailed_results": {
            model: [
                {k: v for k, v in r.items() if k != "generated_code"}
                for r in results
            ]
            for model, results in all_results.items()
        },
        "raw_outputs": all_raw_outputs,
        "benchmark_prompts": [
            {k: v for k, v in p.items() if k != "reference_solution"}
            for p in BENCHMARK_PROMPTS
        ]
    }
    
    # Save locally
    with open("/app/benchmark_results.json", "w") as f:
        json.dump(output, f, indent=2, default=str)
    
    with open("/app/README.md", "w") as f:
        f.write(report)
    
    # Upload to Hub
    try:
        print("\nUploading results to Hub...")
        
        api.upload_file(
            path_or_fileobj="/app/benchmark_results.json",
            path_in_repo="benchmark_results.json",
            repo_id=OUTPUT_REPO,
            repo_type="dataset",
            commit_message="Add benchmark results"
        )
        
        api.upload_file(
            path_or_fileobj="/app/README.md",
            path_in_repo="README.md",
            repo_id=OUTPUT_REPO,
            repo_type="dataset",
            commit_message="Add evaluation report"
        )
        
        # Upload the benchmark code
        for fname in ["benchmark_prompts.py", "evaluation_framework.py", "run_benchmark.py"]:
            fpath = f"/app/{fname}"
            if os.path.exists(fpath):
                api.upload_file(
                    path_or_fileobj=fpath,
                    path_in_repo=f"code/{fname}",
                    repo_id=OUTPUT_REPO,
                    repo_type="dataset",
                    commit_message=f"Add {fname}"
                )
        
        # Upload per-model detailed results
        for model_name, results in all_results.items():
            model_data = {
                "model": model_name,
                "results": results,
            }
            model_path = f"/app/results_{model_name.replace('/', '_')}.json"
            with open(model_path, "w") as f:
                json.dump(model_data, f, indent=2, default=str)
            
            api.upload_file(
                path_or_fileobj=model_path,
                path_in_repo=f"results/{model_name.replace('/', '_')}.json",
                repo_id=OUTPUT_REPO,
                repo_type="dataset",
                commit_message=f"Add {model_name} results"
            )
        
        # Upload leaderboard as separate file
        leaderboard_path = "/app/leaderboard.json"
        with open(leaderboard_path, "w") as f:
            json.dump(leaderboard, f, indent=2)
        
        api.upload_file(
            path_or_fileobj=leaderboard_path,
            path_in_repo="leaderboard.json",
            repo_id=OUTPUT_REPO,
            repo_type="dataset",
            commit_message="Add leaderboard"
        )
        
        print(f"\n✅ All results uploaded to https://huggingface.co/datasets/{OUTPUT_REPO}")
        
    except Exception as e:
        print(f"Upload error: {e}")
        traceback.print_exc()
        print("Results saved locally at /app/benchmark_results.json")
    
    print("\n" + "="*60)
    print("BENCHMARK COMPLETE")
    print("="*60)


if __name__ == "__main__":
    run_benchmark()
