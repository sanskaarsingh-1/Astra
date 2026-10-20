#!/usr/bin/env python3
"""
Astra AI / SatQuery AI — Offline Evaluation CLI
SIH26167 | Space Technology (ISRO SAC)

Reuses the production backend orchestration, specialist inference, and report exporter
to execute offline evaluations without requiring Firebase or the browser frontend.

Usage:
  # Single Optical or SAR image
  python run_eval.py --image evaluation/test_data/representative_cartosat_optical.tif --query "What type of land cover dominates this scene?"

  # Bi-temporal change pair
  python run_eval.py --image-a evaluation/test_data/representative_bitemporal_t1.tif --image-b evaluation/test_data/representative_bitemporal_t2.tif --query "What changed between these two dates?"

  # Optical and SAR pair
  python run_eval.py --optical evaluation/test_data/representative_cartosat_optical.tif --sar evaluation/test_data/representative_risat_sar.tif --query "Compare optical and SAR observations."

  # Full manifest batch evaluation
  python run_eval.py --manifest evaluation/evaluation_manifest.json --output-dir evaluation/results
"""

import sys
import os
import argparse
import asyncio
import json
import time
import uuid
from pathlib import Path

# Ensure project root and backend are in python path
ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Import production backend components
from backend.main import _run_investigation, _investigation_store
from backend.report.exporter import export_markdown_report, export_html_report


async def evaluate_single_case(
    case_id: str,
    query: str,
    file_paths: list[Path],
    output_dir: Path,
    report_format: str = "all",
) -> dict:
    """Execute a single evaluation case using the production backend pipeline."""
    job_id = f"eval_{case_id}_{uuid.uuid4().hex[:6]}"
    queue = asyncio.Queue()
    start_time = time.perf_counter()

    print(f"\n================================================================================")
    print(f"CASE: {case_id}")
    print(f"QUERY: \"{query}\"")
    print(f"INPUTS: {[str(p.name) for p in file_paths]}")
    print(f"================================================================================")

    # Check files exist
    missing = [str(p) for p in file_paths if not p.exists()]
    if missing:
        err_msg = f"Missing input files: {missing}"
        print(f"[FAIL] {err_msg}")
        return {
            "case_id": case_id,
            "job_id": job_id,
            "status": "ERROR",
            "error": err_msg,
            "elapsed_seconds": 0.0,
        }

    # Launch background task
    task = asyncio.create_task(_run_investigation(job_id, query, file_paths, queue))

    completed_payload = None
    error_payload = None
    progress_log = []

    while True:
        msg = await queue.get()
        event = msg.get("event")
        raw_data = msg.get("data", "{}")
        try:
            data = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
        except Exception:
            data = {"raw": raw_data}

        if event == "progress":
            step = data.get("step", "working")
            pct = data.get("pct", 0)
            message = data.get("message", step)
            progress_log.append({"step": step, "pct": pct, "message": message})
            print(f"  [{pct:02d}%] {message}")
        elif event == "complete":
            completed_payload = data
            break
        elif event == "error":
            error_payload = data
            break

    await task
    elapsed = time.perf_counter() - start_time

    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "case_id": case_id,
        "job_id": job_id,
        "query": query,
        "inputs": [str(p) for p in file_paths],
        "elapsed_seconds": round(elapsed, 2),
    }

    if error_payload:
        summary["status"] = "ERROR"
        summary["error"] = error_payload
        print(f"\n[FAIL] Evaluation encountered error: {error_payload}")
    elif completed_payload:
        summary["status"] = "COMPLETED"
        report_data = completed_payload.get("report", {})
        evidence_list = completed_payload.get("evidence", [])
        trace_data = completed_payload.get("trace", {})

        # Extract specialists and models used
        steps = trace_data.get("executed_steps", [])
        tools_invoked = [s.get("tool_id") for s in steps]
        models_invoked = list(set([f.get("source_model") for f in evidence_list if f.get("source_model")]))

        summary["tools_invoked"] = tools_invoked
        summary["models_used"] = models_invoked
        summary["overall_confidence"] = trace_data.get("overall_confidence", "HIGH")
        summary["executive_summary"] = report_data.get("executive_summary", "")
        summary["narrative"] = report_data.get("narrative", "")
        summary["trace_step_count"] = len(steps)

        # Print Evaluation Summary
        print(f"\n--- EVALUATION SUMMARY ---")
        print(f"Status:             SUCCESS")
        print(f"Duration:           {elapsed:.2f}s")
        print(f"Specialists/Tools:  {tools_invoked}")
        print(f"Models:             {models_invoked}")
        print(f"Confidence:         {summary['overall_confidence']}")
        print(f"Narrative:          {summary['narrative'][:200]}...")

        # Export Reports
        if job_id in _investigation_store:
            stored_report, stored_evidence, stored_query = _investigation_store[job_id]
            
            if report_format in ("markdown", "all"):
                md_content = export_markdown_report(stored_report, stored_evidence, job_id)
                md_path = output_dir / f"{case_id}_report.md"
                with open(md_path, "w", encoding="utf-8") as f:
                    f.write(md_content)
                summary["markdown_report"] = str(md_path)
                print(f"Saved Markdown:     {md_path}")

            if report_format in ("html", "all"):
                html_content = export_html_report(stored_report, stored_evidence, job_id)
                html_path = output_dir / f"{case_id}_report.html"
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(html_content)
                summary["html_report"] = str(html_path)
                print(f"Saved HTML:         {html_path}")

    # Save JSON summary
    json_path = output_dir / f"{case_id}_result.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"Saved JSON:         {json_path}")

    return summary


def main():
    parser = argparse.ArgumentParser(
        description="Astra AI / SatQuery AI — Offline Evaluation CLI (SIH26167)"
    )
    parser.add_argument("--image", type=str, help="Single optical or SAR image path")
    parser.add_argument("--image-a", type=str, help="Pre-event image path (bi-temporal)")
    parser.add_argument("--image-b", type=str, help="Post-event image path (bi-temporal)")
    parser.add_argument("--optical", type=str, help="Optical image path (optical-SAR)")
    parser.add_argument("--sar", type=str, help="SAR image path (optical-SAR)")
    parser.add_argument("--query", type=str, help="Natural language query")
    parser.add_argument("--manifest", type=str, help="Path to evaluation manifest JSON")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="evaluation/results",
        help="Directory to save evaluation reports and JSON results",
    )
    parser.add_argument(
        "--format",
        choices=["json", "markdown", "all"],
        default="all",
        help="Output report format",
    )

    args = parser.parse_args()
    out_dir = Path(args.output_dir)

    # 1. Manifest mode
    if args.manifest:
        manifest_path = Path(args.manifest)
        if not manifest_path.exists():
            print(f"Error: Manifest file not found: {manifest_path}")
            sys.exit(1)

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)

        cases = manifest_data.get("cases", [])
        print(f"Executing batch evaluation: {len(cases)} cases from {manifest_path}")
        results = []

        async def run_all():
            for c in cases:
                c_id = c["case_id"]
                c_query = c["query"]
                c_inputs = [ROOT_DIR / p for p in c["inputs"]]
                res = await evaluate_single_case(
                    case_id=c_id,
                    query=c_query,
                    file_paths=c_inputs,
                    output_dir=out_dir,
                    report_format=args.format,
                )
                results.append(res)

        asyncio.run(run_all())

        # Master batch summary
        batch_summary_path = out_dir / "batch_evaluation_summary.json"
        total = len(results)
        passed = sum(1 for r in results if r.get("status") in ("COMPLETED", "ERROR" if "FAILSAFE" in r.get("case_id", "") else ""))
        with open(batch_summary_path, "w", encoding="utf-8") as f:
            json.dump({
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
                "total_cases": total,
                "passed_or_handled": len(results),
                "results": results
            }, f, indent=2)

        print(f"\n================================================================================")
        print(f"BATCH EVALUATION COMPLETED: {len(results)}/{len(cases)} cases processed")
        print(f"Master Summary saved to: {batch_summary_path}")
        print(f"================================================================================\n")
        return

    # 2. Direct CLI input mode
    if not args.query:
        print("Error: --query is required when running single or paired evaluation.")
        parser.print_help()
        sys.exit(1)

    file_paths = []
    if args.image:
        file_paths.append(Path(args.image))
    elif args.image_a and args.image_b:
        file_paths.extend([Path(args.image_a), Path(args.image_b)])
    elif args.optical and args.sar:
        file_paths.extend([Path(args.optical), Path(args.sar)])
    else:
        print("Error: Please provide --image, or --image-a and --image-b, or --optical and --sar.")
        parser.print_help()
        sys.exit(1)

    case_id = f"custom_eval_{int(time.time())}"
    asyncio.run(
        evaluate_single_case(
            case_id=case_id,
            query=args.query,
            file_paths=file_paths,
            output_dir=out_dir,
            report_format=args.format,
        )
    )


if __name__ == "__main__":
    main()
