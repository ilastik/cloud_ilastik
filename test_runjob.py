from pprint import pprint
from hpc import IlastikJobSpec, HpcEnvironment, JobResources
from pathlib import Path

jobspec = IlastikJobSpec(
    hpc_environment=HpcEnvironment(),
    ilp_project=Path("/home/tomaz/unicore_stuff/MyProject.ilp"),
    raw_data_url="https://object.cscs.ch/v1/AUTH_2dc0b65279674a42833a064ce3677297/datasources/e15e4048955ed04112d2652d5a8ce587/317_8_CamKII_tTA_lacZ_Xgal_s134_1.4.n5.tar",
    result_endpoint="http://web.ilastik.org/v1/batch/jobs/external",
    Resources=JobResources(
        CPUs=3,
        Memory="32G"
    )
)

#IlastikJobSpec.ensure_valid_token()
print(repr(jobspec))
job = jobspec.run()
dlist = job.working_dir.listdir()

