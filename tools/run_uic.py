import os
import sys
import subprocess
from pathlib import Path

def run_command(cmd_list, ui_file, py_file):
    venv_bin_path = Path(sys.executable).parent
    env = os.environ.copy()
    env["PATH"] = str(venv_bin_path) + os.pathsep + env["PATH"]
    print(f"Running command: {' '.join(cmd_list)} for {ui_file}")
    try:
        subprocess.run(cmd_list, env=env, check=True)
        print(f"Successfully processed {py_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error processing {py_file}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    ui_file = sys.argv[1]
    py_file = ui_file.replace(".ui", ".py")

    # Run pyside6-uic
    uic_cmd = ["/home/alessio/Progetti/Rare/build_venv/bin/pyside6-uic", ui_file, "-a", "-o", py_file]
    run_command(uic_cmd, ui_file, py_file)

    # Run ruff
    ruff_cmd = ["/home/alessio/Progetti/Rare/build_venv/bin/ruff", "check", "--fix", py_file]
    run_command(ruff_cmd, ui_file, py_file)
