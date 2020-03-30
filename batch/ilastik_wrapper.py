#!/usr/bin/env python3

"""ilastik wrapper script for HPC server."""

import json
import logging
import os
import re
import subprocess
import time
from urllib.parse import urljoin

import requests

logging.basicConfig(format="%(asctime)-30s %(filename)-20s %(levelname)-10s %(message)s", level=logging.INFO)
logging.Formatter.converter = time.gmtime
logging.Formatter.default_time_format = "%Y-%m-%dT%H:%M:%S"
logging.Formatter.default_msec_format = "%s.%03dZ"

log = logging.getLogger(__name__)


def main():
    os.environ["PATH"] = os.pathsep.join(
        [
            os.path.expanduser("~/miniconda3/envs/ildev/bin"),
            os.path.expanduser("~/source/ilastik-meta/ilastik"),
            os.environ["PATH"],
        ]
    )
    os.environ["PYTHONPATH"] = os.path.expanduser("~/source/ndstructs")
    os.environ["HDF5_USE_FILE_LOCKING"] = "FALSE"

    with open("config.json") as f:
        config = json.load(f)
    log.info("config %s", config)

    job_id = os.path.basename(os.getcwd())

    input_prefix = "/".join([config["input_path"], config.get("input_group", "")]).strip("/")
    run(["swift", "--quiet", "download", "--prefix", input_prefix, "--output-dir", "input", config["input_bucket"]])

    os.makedirs("output", mode=0o755, exist_ok=True)
    output_name = re.sub(r"\W", "-", config["ilastik"]["export_source"], flags=re.ASCII).lower() + ".n5"
    output_path = os.path.join("output", output_name)

    ilastik_args = ["ilastik.py", "--headless", "--distributed"]
    ilastik_args += ["--raw_data", os.path.join("input", config["input_path"])]
    ilastik_args += ["--output_filename_format", output_path]
    for k, v in sorted(config["ilastik"].items()):
        ilastik_args += [f"--{k}", str(v)]
    run(ilastik_args, nodes=config["node_count"])

    run(["swift", "--quiet", "upload", "--object-name", job_id, config["output_bucket"], output_path])

    with open(os.path.join(output_path, "exported_data", "attributes.json")) as f:
        output_attrs = json.load(f)

    result_url = urljoin(
        os.environ["OS_STORAGE_URL"] + "/", "/".join([config["output_bucket"], job_id, output_name, "exported_data"]),
    )

    report_url = urljoin(config["report_url_prefix"] + "/", job_id + "/")
    report_payload = {
        "status": "done",
        "result_url": result_url,
        "name": output_name,
        "dtype": output_attrs["dataType"],
        **{f"size_{k}": v for k, v in zip(output_attrs["axes"], output_attrs["dimensions"])},
    }

    log.info("report_url %r", report_url)
    log.info("report_payload %s", report_payload)
    report_response = requests.put(report_url, json=report_payload)
    report_response.raise_for_status()


def run(args, *, nodes=1):
    slurm_args = ["srun", "--constraint", "mc", "--nodes", str(nodes), *args]
    log.info("run %s", slurm_args)
    subprocess.run(slurm_args, check=True)


if __name__ == "__main__":
    main()
