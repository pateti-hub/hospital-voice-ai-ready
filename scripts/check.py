import compileall
import subprocess
import sys

assert compileall.compile_dir("app", quiet=1)
print("Python syntax: OK")
try:
    subprocess.run([sys.executable, "-m", "pytest", "-q"], check=True)
except (subprocess.CalledProcessError, FileNotFoundError):
    raise
