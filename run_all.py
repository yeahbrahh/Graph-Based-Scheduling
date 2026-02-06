#!/usr/bin/env python3
"""
Master script to run the complete exam scheduling workflow:
1. Generate schedule (scheduler.py)
2. Verify schedule (verify.py)
3. Create visualizations (visualize.py)
"""

import subprocess
import sys
import os
from datetime import datetime

def print_header(text):
    """Print a formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")

def run_command(description, command):
    """Run a command and handle errors"""
    print(f"▶ {description}...")
    print(f"  Command: {' '.join(command)}\n")
    
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Print output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        
        print(f"✅ {description} completed successfully!\n")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ ERROR: {description} failed!")
        print(f"Exit code: {e.returncode}")
        if e.stdout:
            print("Output:", e.stdout)
        if e.stderr:
            print("Error:", e.stderr, file=sys.stderr)
        return False
    except FileNotFoundError:
        print(f"❌ ERROR: Python executable not found!")
        print("Make sure Python is installed and in your PATH")
        return False

def main():
    start_time = datetime.now()
    
    # Print welcome banner
    print("\n" + "=" * 70)
    print("  🎓 FINAL EXAM SCHEDULER - COMPLETE WORKFLOW")
    print("=" * 70)
    print(f"  Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # Get Python executable
    python_exe = sys.executable
    
    # Check if data files exist
    required_files = ['classes.ttl', 'rooms.ttl', 'students.ttl']
    missing_files = [f for f in required_files if not os.path.exists(f)]
    
    if missing_files:
        print("\n❌ ERROR: Missing required data files:")
        for f in missing_files:
            print(f"  - {f}")
        print("\nMake sure you run this script from the project directory!")
        sys.exit(1)
    
    print("\n✅ All required data files found")
    
    # Step 1: Generate Schedule
    print_header("STEP 1/3: Generating Exam Schedule")
    if not run_command("Schedule generation", [python_exe, "scheduler.py"]):
        print("\n❌ Workflow stopped due to error in schedule generation")
        sys.exit(1)
    
    # Check if schedule.json was created
    if not os.path.exists("schedule.json"):
        print("❌ ERROR: schedule.json was not created!")
        sys.exit(1)
    
    # Step 2: Verify Schedule
    print_header("STEP 2/3: Verifying Schedule")
    if not run_command("Schedule verification", [python_exe, "verify.py", "schedule.json"]):
        print("\n❌ Workflow stopped due to verification errors")
        print("   Please check the schedule for constraint violations")
        sys.exit(1)
    
    # Step 3: Create Visualizations
    print_header("STEP 3/3: Creating Visualizations")
    if not run_command("Visualization generation", [python_exe, "visualize.py"]):
        print("\n⚠️  Warning: Visualization failed, but schedule is still valid")
        print("   You may need to install matplotlib: pip install matplotlib")
    
    # Final summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print("\n" + "=" * 70)
    print("  🎉 WORKFLOW COMPLETED SUCCESSFULLY!")
    print("=" * 70)
    print(f"\n  Total time: {duration:.2f} seconds")
    print(f"  Finished at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("\n📂 Generated Files:")
    output_files = {
        'schedule.json': 'Exam schedule (JSON)',
        'exam_schedule_visualization.png': 'Timeline visualization (PNG)',
        'schedule_simple.html': 'Simple HTML schedule'
    }
    
    for filename, description in output_files.items():
        if os.path.exists(filename):
            size = os.path.getsize(filename)
            if size > 1024 * 1024:
                size_str = f"{size / (1024 * 1024):.2f} MB"
            elif size > 1024:
                size_str = f"{size / 1024:.2f} KB"
            else:
                size_str = f"{size} bytes"
            print(f"  ✅ {filename:35} ({size_str}) - {description}")
        else:
            print(f"  ⚠️  {filename:35} (not created)")
    
    print("\n💡 Next Steps:")
    print("  • Open schedule_simple.html in your browser for an easy-to-read view")
    print("  • Check exam_schedule_visualization.png for the timeline chart")
    print("  • Review schedule.json for the raw data")
    
    print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Workflow interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
