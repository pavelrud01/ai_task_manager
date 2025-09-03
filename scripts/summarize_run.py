#!/usr/bin/env python3
"""
scripts/summarize_run.py
Generate comprehensive summary report for AI Marketing Agent run

This script analyzes a completed run and generates a detailed summary
with links to key artifacts, statistics, and quality metrics.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional


class RunSummarizer:
    def __init__(self, run_id: Optional[str] = None):
        self.run_id = run_id
        self.run_dir: Optional[Path] = None
        self.summary: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "run_id": None,
            "artifacts": {},
            "statistics": {},
            "quality_metrics": {},
            "gaps": [],
            "recommendations": []
        }

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

    def analyze_artifact(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a single artifact file."""
        analysis = {
            "file": str(file_path),
            "size": file_path.stat().st_size if file_path.exists() else 0,
            "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat() if file_path.exists() else None,
            "type": file_path.suffix,
            "content_analysis": {}
        }
        
        if not file_path.exists():
            return analysis
        
        try:
            if file_path.suffix == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                analysis["content_analysis"] = {
                    "is_valid_json": True,
                    "top_level_keys": list(data.keys()) if isinstance(data, dict) else [],
                    "has_evidence_refs": '"evidence_refs"' in json.dumps(data, ensure_ascii=False),
                    "uncertainty": data.get('uncertainty', None),
                    "hitl_required": data.get('hitl_required', False)
                }
                
                # Count specific elements based on file type
                if 'jobs' in data:
                    analysis["content_analysis"]["jobs_count"] = len(data['jobs']) if isinstance(data['jobs'], list) else 0
                if 'segments' in data:
                    analysis["content_analysis"]["segments_count"] = len(data['segments']) if isinstance(data['segments'], list) else 0
                if 'decision_maps' in data:
                    analysis["content_analysis"]["decision_maps_count"] = len(data['decision_maps']) if isinstance(data['decision_maps'], list) else 0
                    
            elif file_path.suffix == '.md':
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                analysis["content_analysis"] = {
                    "word_count": len(content.split()),
                    "line_count": len(content.splitlines()),
                    "has_evidence_refs": 'evidence' in content.lower(),
                    "has_headers": content.count('#') > 0,
                    "has_lists": content.count('-') > 0 or content.count('*') > 0
                }
                
        except Exception as e:
            analysis["content_analysis"]["error"] = str(e)
        
        return analysis

    def calculate_statistics(self) -> Dict[str, Any]:
        """Calculate overall statistics for the run."""
        stats = {
            "total_artifacts": 0,
            "json_artifacts": 0,
            "markdown_artifacts": 0,
            "total_size_bytes": 0,
            "total_jobs": 0,
            "total_segments": 0,
            "total_decision_maps": 0,
            "artifacts_with_evidence": 0,
            "high_uncertainty_count": 0,
            "hitl_interventions": 0
        }
        
        for artifact_name, artifact_info in self.summary["artifacts"].items():
            stats["total_artifacts"] += 1
            stats["total_size_bytes"] += artifact_info.get("size", 0)
            
            if artifact_info.get("type") == ".json":
                stats["json_artifacts"] += 1
            elif artifact_info.get("type") == ".md":
                stats["markdown_artifacts"] += 1
            
            content_analysis = artifact_info.get("content_analysis", {})
            
            if content_analysis.get("has_evidence_refs"):
                stats["artifacts_with_evidence"] += 1
            
            if content_analysis.get("uncertainty", 0) > 0.7:
                stats["high_uncertainty_count"] += 1
            
            if content_analysis.get("hitl_required"):
                stats["hitl_interventions"] += 1
            
            # Aggregate counts
            stats["total_jobs"] += content_analysis.get("jobs_count", 0)
            stats["total_segments"] += content_analysis.get("segments_count", 0)
            stats["total_decision_maps"] += content_analysis.get("decision_maps_count", 0)
        
        return stats

    def identify_gaps(self) -> List[str]:
        """Identify potential gaps or issues in the run."""
        gaps = []
        
        # Check for missing core artifacts
        required_artifacts = [
            "step_04_jtbd.json",
            "step_05_segments.json", 
            "step_06_decision_mapping.json"
        ]
        
        for artifact in required_artifacts:
            if artifact not in self.summary["artifacts"]:
                gaps.append(f"Missing required artifact: {artifact}")
        
        # Check for evidence references
        evidence_required = ["step_04_jtbd.json", "step_05_segments.json", "step_06_decision_mapping.json"]
        for artifact in evidence_required:
            if artifact in self.summary["artifacts"]:
                if not self.summary["artifacts"][artifact].get("content_analysis", {}).get("has_evidence_refs"):
                    gaps.append(f"Missing evidence references in {artifact}")
        
        # Check for low job/segment counts
        stats = self.summary["statistics"]
        if stats.get("total_jobs", 0) < 3:
            gaps.append("Low number of jobs identified (less than 3)")
        
        if stats.get("total_segments", 0) < 2:
            gaps.append("Low number of segments identified (less than 2)")
        
        # Check for high uncertainty
        if stats.get("high_uncertainty_count", 0) > 0:
            gaps.append(f"High uncertainty detected in {stats['high_uncertainty_count']} artifacts")
        
        return gaps

    def generate_recommendations(self) -> List[str]:
        """Generate recommendations for improving the run."""
        recommendations = []
        
        stats = self.summary["statistics"]
        
        # Evidence recommendations
        evidence_coverage = (stats.get("artifacts_with_evidence", 0) / max(stats.get("total_artifacts", 1), 1)) * 100
        if evidence_coverage < 80:
            recommendations.append("Improve evidence reference coverage - aim for 80%+ of artifacts")
        
        # Content recommendations
        if stats.get("total_jobs", 0) < 5:
            recommendations.append("Consider conducting more interviews to identify additional jobs")
        
        if stats.get("total_segments", 0) < 3:
            recommendations.append("Review segmentation criteria to identify more distinct segments")
        
        # Quality recommendations
        if stats.get("high_uncertainty_count", 0) > 0:
            recommendations.append("Review high-uncertainty artifacts and consider additional validation")
        
        if stats.get("hitl_interventions", 0) > 0:
            recommendations.append("Consider automating steps that required human intervention")
        
        return recommendations

    def generate_summary(self) -> str:
        """Generate the complete summary report."""
        report_lines = [
            "# AI Marketing Agent Run Summary",
            "",
            f"**Run ID**: {self.summary['run_id']}",
            f"**Generated**: {self.summary['timestamp']}",
            f"**Run Directory**: {self.run_dir}",
            "",
            "## Overview",
            "",
            f"This summary provides a comprehensive analysis of the AI Marketing Agent run {self.summary['run_id']}.",
            "",
            "## Artifacts",
            "",
            "### Core Artifacts",
            ""
        ]
        
        # Core artifacts
        core_artifacts = [
            "step_04_jtbd.json",
            "step_05_segments.json", 
            "step_06_decision_mapping.json"
        ]
        
        for artifact in core_artifacts:
            if artifact in self.summary["artifacts"]:
                info = self.summary["artifacts"][artifact]
                report_lines.extend([
                    f"#### {artifact}",
                    f"- **Size**: {info.get('size', 0):,} bytes",
                    f"- **Modified**: {info.get('modified', 'Unknown')}",
                    f"- **Evidence Refs**: {'✅' if info.get('content_analysis', {}).get('has_evidence_refs') else '❌'}",
                ])
                
                content_analysis = info.get("content_analysis", {})
                if "jobs_count" in content_analysis:
                    report_lines.append(f"- **Jobs Count**: {content_analysis['jobs_count']}")
                if "segments_count" in content_analysis:
                    report_lines.append(f"- **Segments Count**: {content_analysis['segments_count']}")
                if "decision_maps_count" in content_analysis:
                    report_lines.append(f"- **Decision Maps Count**: {content_analysis['decision_maps_count']}")
                
                report_lines.append("")
        
        # Additional artifacts
        additional_artifacts = [name for name in self.summary["artifacts"].keys() if name not in core_artifacts]
        if additional_artifacts:
            report_lines.extend([
                "### Additional Artifacts",
                ""
            ])
            
            for artifact in additional_artifacts:
                info = self.summary["artifacts"][artifact]
                report_lines.extend([
                    f"- **{artifact}**: {info.get('size', 0):,} bytes",
                ])
            
            report_lines.append("")
        
        # Statistics
        stats = self.summary["statistics"]
        report_lines.extend([
            "## Statistics",
            "",
            f"- **Total Artifacts**: {stats.get('total_artifacts', 0)}",
            f"- **JSON Artifacts**: {stats.get('json_artifacts', 0)}",
            f"- **Markdown Artifacts**: {stats.get('markdown_artifacts', 0)}",
            f"- **Total Size**: {stats.get('total_size_bytes', 0):,} bytes",
            f"- **Total Jobs**: {stats.get('total_jobs', 0)}",
            f"- **Total Segments**: {stats.get('total_segments', 0)}",
            f"- **Total Decision Maps**: {stats.get('total_decision_maps', 0)}",
            f"- **Artifacts with Evidence**: {stats.get('artifacts_with_evidence', 0)}",
            f"- **High Uncertainty Count**: {stats.get('high_uncertainty_count', 0)}",
            f"- **HITL Interventions**: {stats.get('hitl_interventions', 0)}",
            ""
        ])
        
        # Quality metrics
        report_lines.extend([
            "## Quality Metrics",
            "",
            f"- **Evidence Coverage**: {(stats.get('artifacts_with_evidence', 0) / max(stats.get('total_artifacts', 1), 1)) * 100:.1f}%",
            f"- **Average Jobs per Artifact**: {stats.get('total_jobs', 0) / max(stats.get('json_artifacts', 1), 1):.1f}",
            f"- **Average Segments per Artifact**: {stats.get('total_segments', 0) / max(stats.get('json_artifacts', 1), 1):.1f}",
            ""
        ])
        
        # Gaps
        if self.summary["gaps"]:
            report_lines.extend([
                "## Identified Gaps",
                ""
            ])
            
            for gap in self.summary["gaps"]:
                report_lines.append(f"- ❌ {gap}")
            
            report_lines.append("")
        
        # Recommendations
        if self.summary["recommendations"]:
            report_lines.extend([
                "## Recommendations",
                ""
            ])
            
            for rec in self.summary["recommendations"]:
                report_lines.append(f"- 💡 {rec}")
            
            report_lines.append("")
        
        # Links
        report_lines.extend([
            "## Quick Links",
            "",
            f"- **Run Directory**: `{self.run_dir}`",
            f"- **Artifacts**: `{self.run_dir}/*`",
            f"- **Smoke Test Report**: `{self.run_dir}/smoke_report.md` (if available)",
            ""
        ])
        
        report_lines.extend([
            "---",
            "*Generated by AI Marketing Agent Run Summarizer*"
        ])
        
        return "\n".join(report_lines)

    def run(self) -> bool:
        """Run the complete summarization process."""
        try:
            # Find run directory
            if self.run_id:
                self.run_dir = Path("artifacts") / self.run_id
                if not self.run_dir.exists():
                    print(f"❌ Run directory not found: {self.run_dir}")
                    return False
            else:
                self.run_dir = self.find_latest_run()
                self.run_id = self.run_dir.name
            
            self.summary["run_id"] = self.run_id
            print(f"📁 Analyzing run: {self.run_id}")
            print(f"📂 Run directory: {self.run_dir}")
            
            # Analyze all artifacts
            print("🔍 Analyzing artifacts...")
            for file_path in self.run_dir.rglob("*"):
                if file_path.is_file() and not file_path.name.startswith('.'):
                    relative_path = file_path.relative_to(self.run_dir)
                    self.summary["artifacts"][str(relative_path)] = self.analyze_artifact(file_path)
            
            # Calculate statistics
            print("📊 Calculating statistics...")
            self.summary["statistics"] = self.calculate_statistics()
            
            # Identify gaps
            print("🔍 Identifying gaps...")
            self.summary["gaps"] = self.identify_gaps()
            
            # Generate recommendations
            print("💡 Generating recommendations...")
            self.summary["recommendations"] = self.generate_recommendations()
            
            # Generate and save report
            print("📄 Generating summary report...")
            report_content = self.generate_summary()
            
            summary_path = self.run_dir / "summary.md"
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            print(f"✅ Summary report saved: {summary_path}")
            
            # Print summary to console
            print("\n" + "=" * 60)
            print("📋 RUN SUMMARY")
            print("=" * 60)
            print(f"Run ID: {self.run_id}")
            print(f"Total Artifacts: {self.summary['statistics'].get('total_artifacts', 0)}")
            print(f"Total Jobs: {self.summary['statistics'].get('total_jobs', 0)}")
            print(f"Total Segments: {self.summary['statistics'].get('total_segments', 0)}")
            print(f"Evidence Coverage: {(self.summary['statistics'].get('artifacts_with_evidence', 0) / max(self.summary['statistics'].get('total_artifacts', 1), 1)) * 100:.1f}%")
            print(f"Gaps Identified: {len(self.summary['gaps'])}")
            print(f"Recommendations: {len(self.summary['recommendations'])}")
            print(f"Summary Report: {summary_path}")
            
            return True
            
        except Exception as e:
            print(f"❌ Summarization failed: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Main entry point for run summarizer."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate comprehensive summary for AI Marketing Agent run")
    parser.add_argument("--run-id", help="Specific run ID to analyze (default: latest)")
    parser.add_argument("--output", help="Output file path (default: artifacts/<run_id>/summary.md)")
    
    args = parser.parse_args()
    
    try:
        summarizer = RunSummarizer(args.run_id)
        success = summarizer.run()
        
        if success:
            print("\n🎉 Run summarization completed successfully!")
            sys.exit(0)
        else:
            print("\n💥 Run summarization failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Summarization interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Summarization failed with exception: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()


