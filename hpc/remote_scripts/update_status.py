#!/usr/bin/env python

"""Update the current job status by sending an HTTP request."""

import argparse
import json
import pathlib
import requests
import urllib.parse

# FIXME: The account name can change.
ACCOUNT = "AUTH_2dc0b65279674a42833a064ce3677297"


def parse_args():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "endpoint", help="base URL for reporting the job status, without the job ID, with the trailing slash"
    )
    ap.add_argument("job", help="unicore job ID")
    ap.add_argument("status", help="job status", choices="created running done failed".split())
    ap.add_argument(
        "--output",
        metavar="DIR",
        help="local, top-level N5 directory with results; required when status is 'done'",
        type=pathlib.Path,
    )
    ap.add_argument(
        "--bucket", metavar="NAME", help="remote bucket name with the output contents; required when status is 'done'"
    )

    args = ap.parse_args()
    if args.status == "done" and not all((args.output, args.bucket)):
        ap.error("'--output' and '--bucket' are required when status is 'done'")

    return args


def main():
    args = parse_args()
    data = {"status": args.status}

    if args.status == "done":
        with open(args.output / "exported_data" / "attributes.json") as fd:
            attrs = json.loads(fd.read())
        data = {
            **data,
            "result_url": f"https://object.cscs.ch/v1/{ACCOUNT}/{args.bucket}/{args.output.name}/exported_data",
            "name": args.output.name,
            "dtype": attrs["dataType"],
            **{f"size_{k}": v for k, v in zip(attrs["axes"], attrs["dimensions"])},
        }

    url = urllib.parse.urljoin(args.endpoint, args.job)
    print(f"Posting job report back to {url}")
    print(json.dumps(data, indent=4))
    result = requests.post(url, json=data)
    print(f"Report response: {result.status_code}")
    print(result.text)


if __name__ == "__main__":
    main()
