"""Demo launcher for anytime inference.

Run with: python -m anytime.demo
"""

import subprocess
import sys


def main():
    """Launch the Streamlit demo app."""
    # Get the directory containing this module
    from pathlib import Path
    module_dir = Path(__file__).resolve().parent
    candidates = [
        module_dir / "demos" / "app.py",
        module_dir.parent / "demos" / "app.py",
    ]
    app_path = next((path for path in candidates if path.exists()), None)
    if app_path is None:
        print("Error: Demo app not found in expected locations.", file=sys.stderr)
        sys.exit(1)

    # Launch streamlit
    cmd = [sys.executable, "-m", "streamlit", "run", str(app_path)]
    print(f"Launching: {' '.join(cmd)}")
    subprocess.run(cmd)


if __name__ == "__main__":
    main()
