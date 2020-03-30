#!/usr/bin/env python3

"""ilastik wrapper script for HPC server."""

import json
import logging
import os
import re
import subprocess
import time
from pathlib import Path
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

    job_id = Path.cwd().name
    config = json.loads(Path("config.json").read_text())
    log.info("config %s", config)

    inputs = download_inputs(config["inputs"])
    output_path = run_ilastik(inputs=inputs, params=config["ilastik"], node_count=config["node_count"])
    run(["swift", "--quiet", "upload", "--object-name", job_id, config["output_bucket"], str(output_path)])
    report_result(config=config, output_path=output_path, job_id=job_id)


def download_inputs(inputs):
    res = {}

    for k, v in sorted(inputs.items()):
        bucket = v["bucket"]
        path = v["path"]
        group = v.get("group", "")

        prefix = f"{path}/{group}".strip("/")
        output_dir = Path("input", bucket)
        run(["swift", "--quiet", "download", "--prefix", prefix, "--output-dir", str(output_dir), bucket])

        res[k] = output_dir.joinpath(*path.split("/"))

    return res


def run_ilastik(*, inputs, params, node_count):
    os.makedirs("output", mode=0o755)

    output_name = re.sub(r"\W", "-", params["export_source"], flags=re.ASCII).lower() + ".n5"
    output_path = Path("output", output_name)

    ilastik_args = ["ilastik.py", "--headless", "--distributed", "--output_filename_format", str(output_path)]
    for k, v in sorted(inputs.items()) + sorted(params.items()):
        ilastik_args += [f"--{k}", str(v)]

    run(ilastik_args, nodes=node_count)

    return output_path


def report_result(*, config, output_path, job_id):
    result_url = urljoin(
        os.environ["OS_STORAGE_URL"] + "/", f"{config['output_bucket']}/{job_id}/{output_path.name}/exported_data"
    )
    output_attrs = json.loads((output_path / "exported_data/attributes.json").read_text())

    url = urljoin(config["report_url_prefix"] + "/", job_id + "/")
    payload = {
        "status": "done",
        "result_url": result_url,
        "name": output_path.name,
        "dtype": output_attrs["dataType"],
        **{f"size_{k}": v for k, v in zip(output_attrs["axes"], output_attrs["dimensions"])},
    }

    log.info("report url %r", url)
    log.info("report payload %s", payload)
    response = requests.put(url, json=payload)
    response.raise_for_status()


def run(args, *, nodes=1):
    # slurm_args = ["srun", "--constraint", "mc", "--nodes", str(nodes), *args]
    slurm_args = ["srun", "--constraint", "mc", "--nodes", "1", *args]
    log.info("run %s", slurm_args)
    subprocess.run(slurm_args, check=True)


if __name__ == "__main__":
    main()
