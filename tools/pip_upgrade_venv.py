import pkg_resources
from subprocess import call

for dist in pkg_resources.working_set:
    call(f"python -m pip install --upgrade {dist.project_name}", shell=True)
