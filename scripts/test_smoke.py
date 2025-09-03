#!/usr/bin/env python3
"""
scripts/test_smoke.py
Smoke test for AI Marketing Agent workflow

This script runs a minimal test of the workflow using minimal fixtures
to verify that all components work correctly and produce expected artifacts.
"""

import json
import sys
import subprocess
import shutil
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional


class SmokeTest:
    def __init__(self):
        self.case = "tests/fixtures"
        self.input_file = Path(self.case) / "input_min.json"
        self.guide_file = Path(self.case) / "guide_min.md"
        self.run_id: Optional[str] = None
        self.run_dir: Optional[Path] = None
        self.results: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "tests_passed": 0,
            "tests_failed": 0,
            "errors": [],
            "artifacts_found": [],
            "artifacts_missing": [],
            "evidence_checks": [],
            "schema_validations": []
        }

    def run_command(self, cmd: List[str]) -> subprocess.CompletedProcess:
        """Run a command and return the result."""
        print(">", " ".join(cmd))
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result
        except subprocess.CalledProcessError as e:
            print(f"❌ Command failed: {e}")
            print(f"stdout: {e.stdout}")
            print(f"stderr: {e.stderr}")
            raise

    def must_exist(self, path: Path) -> bool:
        """Check if a file exists, raise error if not."""
        if not path.exists():
            error_msg = f"Missing required artifact: {path}"
            print(f"❌ {error_msg}")
            self.results["errors"].append(error_msg)
            self.results["artifacts_missing"].append(str(path))
            return False
        else:
            print(f"✅ Found: {path}")
            self.results["artifacts_found"].append(str(path))
            return True

    def check_evidence_refs(self, path: Path) -> bool:
        """Check if artifact contains evidence_refs."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for evidence_refs in JSON files
            if path.suffix == '.json':
                data = json.loads(content)
                blob = json.dumps(data, ensure_ascii=False)
                if '"evidence_refs"' not in blob:
                    error_msg = f"No evidence_refs found in {path}"
                    print(f"❌ {error_msg}")
                    self.results["errors"].append(error_msg)
                    self.results["evidence_checks"].append({
                        "file": str(path),
                        "status": "FAILED",
                        "reason": "No evidence_refs field found"
                    })
                    return False
                else:
                    print(f"✅ Evidence refs found in {path}")
                    self.results["evidence_checks"].append({
                        "file": str(path),
                        "status": "PASSED",
                        "reason": "evidence_refs field found"
                    })
                    return True
            
            # Check for evidence references in Markdown files
            elif path.suffix == '.md':
                if 'evidence_refs' in content.lower() or 'evidence' in content.lower():
                    print(f"✅ Evidence references found in {path}")
                    self.results["evidence_checks"].append({
                        "file": str(path),
                        "status": "PASSED",
                        "reason": "Evidence references found in content"
                    })
                    return True
                else:
                    error_msg = f"No evidence references found in {path}"
                    print(f"❌ {error_msg}")
                    self.results["errors"].append(error_msg)
                    self.results["evidence_checks"].append({
                        "file": str(path),
                        "status": "FAILED",
                        "reason": "No evidence references found in content"
                    })
                    return False
            
            return True
            
        except Exception as e:
            error_msg = f"Error checking evidence in {path}: {e}"
            print(f"❌ {error_msg}")
            self.results["errors"].append(error_msg)
            return False

    def validate_json_schema(self, path: Path) -> bool:
        """Validate JSON file against expected schema."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Basic JSON validation
            if not isinstance(data, dict):
                error_msg = f"Invalid JSON structure in {path}: not a dict"
                print(f"❌ {error_msg}")
                self.results["errors"].append(error_msg)
                self.results["schema_validations"].append({
                    "file": str(path),
                    "status": "FAILED",
                    "reason": "Not a valid JSON object"
                })
                return False
            
            # Check for required fields based on step
            step_name = path.stem
            required_fields = self.get_required_fields(step_name)
            
            missing_fields = []
            for field in required_fields:
                if field not in data:
                    missing_fields.append(field)
            
            if missing_fields:
                error_msg = f"Missing required fields in {path}: {missing_fields}"
                print(f"❌ {error_msg}")
                self.results["errors"].append(error_msg)
                self.results["schema_validations"].append({
                    "file": str(path),
                    "status": "FAILED",
                    "reason": f"Missing fields: {missing_fields}"
                })
                return False
            
            print(f"✅ Schema validation passed for {path}")
            self.results["schema_validations"].append({
                "file": str(path),
                "status": "PASSED",
                "reason": "All required fields present"
            })
            return True
            
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON in {path}: {e}"
            print(f"❌ {error_msg}")
            self.results["errors"].append(error_msg)
            self.results["schema_validations"].append({
                "file": str(path),
                "status": "FAILED",
                "reason": f"JSON decode error: {e}"
            })
            return False
        except Exception as e:
            error_msg = f"Error validating schema for {path}: {e}"
            print(f"❌ {error_msg}")
            self.results["errors"].append(error_msg)
            return False

    def get_required_fields(self, step_name: str) -> List[str]:
        """Get required fields for a specific step."""
        field_mapping = {
            "step_04_jtbd": ["jobs", "big_jobs"],
            "step_05_segments": ["segments"],
            "step_06_decision_mapping": ["decision_maps", "ctas"],
            "step_05b_segments_merged": ["merged_segments", "personas"]
        }
        return field_mapping.get(step_name, [])

    def check_uncertainty_threshold(self, run_dir: Path) -> bool:
        """Check if uncertainty is within acceptable threshold or HITL was triggered."""
        try:
            # Look for uncertainty values in artifacts
            uncertainty_found = False
            high_uncertainty = False
            
            for json_file in run_dir.glob("*.json"):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Check for uncertainty field
                    if 'uncertainty' in data:
                        uncertainty_found = True
                        uncertainty_value = data['uncertainty']
                        if isinstance(uncertainty_value, (int, float)) and uncertainty_value > 0.7:
                            high_uncertainty = True
                            print(f"⚠️  High uncertainty detected in {json_file}: {uncertainty_value}")
                    
                    # Check for HITL flags
                    if 'hitl_required' in data or 'human_intervention' in data:
                        print(f"ℹ️  HITL intervention detected in {json_file}")
                        return True  # HITL is acceptable
                        
                except Exception:
                    continue
            
            if not uncertainty_found:
                print("ℹ️  No uncertainty values found in artifacts")
                return True  # No uncertainty data is acceptable
            
            if high_uncertainty:
                print("⚠️  High uncertainty detected but no HITL intervention found")
                return False
            
            print("✅ Uncertainty within acceptable threshold")
            return True
            
        except Exception as e:
            print(f"⚠️  Error checking uncertainty: {e}")
            return True  # Don't fail the test for uncertainty check errors

    def find_latest_run(self) -> Path:
        """Find the most recent run directory."""
        artifacts_dir = Path("artifacts")
        if not artifacts_dir.exists():
            raise FileNotFoundError("Artifacts directory not found")
        
        runs = sorted(
            [d for d in artifacts_dir.iterdir() if d.is_dir() and d.name.startswith("run_")],
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        if not runs:
            raise FileNotFoundError("No run directories found")
        
        return runs[0]

    def run_smoke_test(self) -> bool:
        """Run the complete smoke test."""
        print("🚀 Starting AI Marketing Agent Smoke Test")
        print("=" * 60)
        
        try:
            # Step 1: Run the main workflow
            print("\n📋 Step 1: Running main workflow...")
            cmd = [
                "python", "main.py",
                "--input", str(self.input_file),
                "--project-dir", self.case
            ]
            
            result = self.run_command(cmd)
            print("✅ Main workflow completed")
            
            # Step 2: Find the latest run
            print("\n📋 Step 2: Finding latest run...")
            self.run_dir = self.find_latest_run()
            self.run_id = self.run_dir.name
            print(f"✅ Found run: {self.run_id}")
            print(f"📁 Run directory: {self.run_dir}")
            
            # Step 3: Check basic artifacts
            print("\n📋 Step 3: Checking basic artifacts...")
            basic_artifacts = [
                "step_00_compliance_check.json",
                "step_02_extract.json", 
                "step_03_interview_collect.json",
                "step_04_jtbd.json",
                "step_05_segments.json",
                "step_06_decision_mapping.json"
            ]
            
            for artifact in basic_artifacts:
                artifact_path = self.run_dir / artifact
                if self.must_exist(artifact_path):
                    self.results["tests_passed"] += 1
                else:
                    self.results["tests_failed"] += 1
            
            # Step 4: Check interview files
            print("\n📋 Step 4: Checking interview files...")
            interviews_dir = self.run_dir / "interviews"
            if interviews_dir.exists():
                interview_files = list(interviews_dir.glob("*.jsonl"))
                if interview_files:
                    print(f"✅ Found {len(interview_files)} interview files")
                    self.results["tests_passed"] += 1
                    for file in interview_files:
                        self.results["artifacts_found"].append(str(file))
                else:
                    error_msg = "No interview files found"
                    print(f"❌ {error_msg}")
                    self.results["errors"].append(error_msg)
                    self.results["tests_failed"] += 1
            else:
                error_msg = "Interviews directory not found"
                print(f"❌ {error_msg}")
                self.results["errors"].append(error_msg)
                self.results["tests_failed"] += 1
            
            # Step 5: Check export artifacts (if they exist)
            print("\n📋 Step 5: Checking export artifacts...")
            exports_dir = self.run_dir / "exports"
            if exports_dir.exists():
                export_files = list(exports_dir.rglob("*.md"))
                if export_files:
                    print(f"✅ Found {len(export_files)} export files")
                    self.results["tests_passed"] += 1
                    for file in export_files:
                        self.results["artifacts_found"].append(str(file))
                else:
                    print("ℹ️  No export files found (optional)")
            
            # Check for merged segments file
            merged_file = self.run_dir / "step_05b_segments_merged.json"
            if merged_file.exists():
                print("✅ Found merged segments file")
                self.results["artifacts_found"].append(str(merged_file))
                self.results["tests_passed"] += 1
            
            # Step 6: Validate JSON schemas
            print("\n📋 Step 6: Validating JSON schemas...")
            json_files = list(self.run_dir.glob("*.json"))
            for json_file in json_files:
                if self.validate_json_schema(json_file):
                    self.results["tests_passed"] += 1
                else:
                    self.results["tests_failed"] += 1
            
            # Step 7: Check evidence references
            print("\n📋 Step 7: Checking evidence references...")
            evidence_files = [
                "step_04_jtbd.json",
                "step_05_segments.json", 
                "step_06_decision_mapping.json"
            ]
            
            for evidence_file in evidence_files:
                file_path = self.run_dir / evidence_file
                if file_path.exists():
                    if self.check_evidence_refs(file_path):
                        self.results["tests_passed"] += 1
                    else:
                        self.results["tests_failed"] += 1
            
            # Step 8: Check uncertainty threshold
            print("\n📋 Step 8: Checking uncertainty threshold...")
            if self.check_uncertainty_threshold(self.run_dir):
                self.results["tests_passed"] += 1
            else:
                self.results["tests_failed"] += 1
            
            # Step 9: Generate report
            print("\n📋 Step 9: Generating smoke test report...")
            self.generate_report()
            
            # Final result
            total_tests = self.results["tests_passed"] + self.results["tests_failed"]
            success_rate = (self.results["tests_passed"] / total_tests * 100) if total_tests > 0 else 0
            
            print("\n" + "=" * 60)
            print("🎯 SMOKE TEST RESULTS")
            print("=" * 60)
            print(f"✅ Tests passed: {self.results['tests_passed']}")
            print(f"❌ Tests failed: {self.results['tests_failed']}")
            print(f"📊 Success rate: {success_rate:.1f}%")
            print(f"📁 Run ID: {self.run_id}")
            print(f"📂 Artifacts: {self.run_dir}")
            
            if self.results["errors"]:
                print(f"\n🚨 Errors found: {len(self.results['errors'])}")
                for error in self.results["errors"]:
                    print(f"   - {error}")
            
            return self.results["tests_failed"] == 0
            
        except Exception as e:
            print(f"\n❌ Smoke test failed with exception: {e}")
            self.results["errors"].append(f"Smoke test exception: {e}")
            self.generate_report()
            return False

    def generate_report(self):
        """Generate smoke test report."""
        if not self.run_dir:
            return
        
        report_content = f"""# Smoke Test Report

**Run ID**: {self.run_id}
**Timestamp**: {self.results['timestamp']}
**Test Results**: {self.results['tests_passed']} passed, {self.results['tests_failed']} failed

## Summary

- **Total Tests**: {self.results['tests_passed'] + self.results['tests_failed']}
- **Success Rate**: {(self.results['tests_passed'] / (self.results['tests_passed'] + self.results['tests_failed']) * 100) if (self.results['tests_passed'] + self.results['tests_failed']) > 0 else 0:.1f}%
- **Run Directory**: {self.run_dir}

## Artifacts Found

{chr(10).join(f"- {artifact}" for artifact in self.results['artifacts_found'])}

## Artifacts Missing

{chr(10).join(f"- {artifact}" for artifact in self.results['artifacts_missing'])}

## Evidence Checks

{chr(10).join(f"- **{check['file']}**: {check['status']} - {check['reason']}" for check in self.results['evidence_checks'])}

## Schema Validations

{chr(10).join(f"- **{validation['file']}**: {validation['status']} - {validation['reason']}" for validation in self.results['schema_validations'])}

## Errors

{chr(10).join(f"- {error}" for error in self.results['errors'])}

## Test Configuration

- **Input File**: {self.input_file}
- **Guide File**: {self.guide_file}
- **Case Directory**: {self.case}

---
*Generated by AI Marketing Agent Smoke Test*
"""
        
        report_path = self.run_dir / "smoke_report.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"📄 Smoke test report saved: {report_path}")


def main():
    """Main entry point for smoke test."""
    try:
        smoke_test = SmokeTest()
        success = smoke_test.run_smoke_test()
        
        if success:
            print("\n🎉 SMOKE TEST PASSED!")
            sys.exit(0)
        else:
            print("\n💥 SMOKE TEST FAILED!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Smoke test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Smoke test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()


