#!/usr/bin/env python3
"""
scripts/run.py
Unified CLI helper for running AI Marketing Agent scenarios

Usage:
    python scripts/run.py --case A
    python scripts/run.py --case B --project-dir projects/CustomCase
    python scripts/run.py --case C --input custom_input.json
"""

import argparse
import sys
import subprocess
import os
from pathlib import Path


def get_python_command():
    """Determine the best Python command to use."""
    if sys.executable:
        return sys.executable
    elif os.system("python3 --version") == 0:
        return "python3"
    elif os.system("python --version") == 0:
        return "python"
    else:
        raise RuntimeError("Python not found. Please install Python 3.12+")


def setup_venv():
    """Set up virtual environment if it doesn't exist."""
    venv_path = Path(".venv")
    
    if not venv_path.exists():
        print("📦 Creating virtual environment...")
        python_cmd = get_python_command()
        result = subprocess.run([python_cmd, "-m", "venv", ".venv"], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Failed to create virtual environment: {result.stderr}")
            return False
    
    return True


def install_dependencies():
    """Install dependencies in virtual environment."""
    print("📚 Installing dependencies...")
    
    # Determine activation script based on OS
    if os.name == 'nt':  # Windows
        pip_cmd = ".venv/Scripts/pip"
    else:  # Unix-like
        pip_cmd = ".venv/bin/pip"
    
    # Upgrade pip
    result = subprocess.run([pip_cmd, "install", "--upgrade", "pip"], 
                          capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Failed to upgrade pip: {result.stderr}")
        return False
    
    # Install requirements
    result = subprocess.run([pip_cmd, "install", "-r", "requirements.txt"], 
                          capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Failed to install dependencies: {result.stderr}")
        return False
    
    return True


def run_main_script(input_file, project_dir):
    """Run the main.py script with given parameters."""
    print("🎯 Running AI Marketing Agent...")
    
    # Determine Python command based on OS
    if os.name == 'nt':  # Windows
        python_cmd = ".venv/Scripts/python"
    else:  # Unix-like
        python_cmd = ".venv/bin/python"
    
    cmd = [python_cmd, "main.py", "--input", str(input_file), "--project-dir", str(project_dir)]
    print(f"Command: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, capture_output=False, text=True)
    return result.returncode


def validate_paths(input_file, project_dir):
    """Validate that required paths exist."""
    if not Path(input_file).exists():
        print(f"❌ Input file not found: {input_file}")
        return False
    
    if not Path(project_dir).exists():
        print(f"❌ Project directory not found: {project_dir}")
        return False
    
    return True


def get_case_config(case):
    """Get configuration for specific case."""
    case_configs = {
        'A': {
            'name': 'Simulate Scenario',
            'project_dir': 'projects/CaseA',
            'input_file': 'projects/CaseA/input.json',
            'description': 'Quick start with simulated interviews for testing workflow'
        },
        'B': {
            'name': 'Ingest Scenario', 
            'project_dir': 'projects/CaseB',
            'input_file': 'projects/CaseB/input.json',
            'description': 'Load existing interview data with follow-up interviews'
        },
        'C': {
            'name': 'Full Run Scenario',
            'project_dir': 'projects/CaseC', 
            'input_file': 'projects/CaseC/input.json',
            'description': 'Complete analysis with seed data and full workflow'
        }
    }
    
    return case_configs.get(case.upper())


def main():
    parser = argparse.ArgumentParser(
        description="Unified CLI helper for AI Marketing Agent scenarios",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/run.py --case A
  python scripts/run.py --case B --project-dir projects/CustomCase
  python scripts/run.py --case C --input custom_input.json
  python scripts/run.py --case A --project-dir projects/MyProject --input projects/MyProject/input.json

Available cases:
  A - Simulate Scenario: Quick start with simulated interviews
  B - Ingest Scenario: Load existing data with follow-ups  
  C - Full Run Scenario: Complete analysis with seed data
        """
    )
    
    parser.add_argument(
        '--case', 
        choices=['A', 'B', 'C', 'a', 'b', 'c'],
        required=True,
        help='Case scenario to run (A, B, or C)'
    )
    
    parser.add_argument(
        '--project-dir',
        type=str,
        help='Project directory path (overrides case default)'
    )
    
    parser.add_argument(
        '--input',
        type=str, 
        help='Input JSON file path (overrides case default)'
    )
    
    parser.add_argument(
        '--skip-setup',
        action='store_true',
        help='Skip virtual environment setup and dependency installation'
    )
    
    args = parser.parse_args()
    
    # Get case configuration
    config = get_case_config(args.case)
    if not config:
        print(f"❌ Invalid case: {args.case}")
        sys.exit(1)
    
    # Determine paths
    project_dir = args.project_dir or config['project_dir']
    input_file = args.input or config['input_file']
    
    print(f"🚀 Starting Case {args.case.upper()}: {config['name']}")
    print(f"Description: {config['description']}")
    print(f"Project Directory: {project_dir}")
    print(f"Input File: {input_file}")
    
    # Validate paths
    if not validate_paths(input_file, project_dir):
        sys.exit(1)
    
    # Setup environment if not skipped
    if not args.skip_setup:
        if not setup_venv():
            sys.exit(1)
        
        if not install_dependencies():
            sys.exit(1)
    
    # Run main script
    exit_code = run_main_script(input_file, project_dir)
    
    if exit_code == 0:
        print("✅ Case completed successfully!")
        print("📋 Check the artifacts directory for results")
        
        # Additional info for Case C
        if args.case.upper() == 'C':
            print("📊 Check the exports directory for detailed reports")
    else:
        print(f"❌ Case failed with exit code: {exit_code}")
        sys.exit(exit_code)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

