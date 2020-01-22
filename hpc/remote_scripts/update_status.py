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
    ap.add_argument(
        "--output",
        required=True,
        metavar="DIR",
        help="local, top-level N5 directory with results",
        type=pathlib.Path,
    )
    ap.add_argument(
        "--bucket",
        required=True,
        metavar="NAME",
        help="remote bucket name with the output contents"
    )
    args = ap.parse_args()
    return args


def main():
    args = parse_args()

    with open(args.output / "exported_data" / "attributes.json") as fd:
        attrs = json.loads(fd.read())
    data = {
        "status": "done",
        "result_url": f"https://object.cscs.ch/v1/{ACCOUNT}/{args.bucket}/{args.output.name}/exported_data",
        "name": args.output.name,
        "dtype": attrs["dataType"],
        **{f"size_{k}": v for k, v in zip(attrs["axes"], attrs["dimensions"])},
    }

    url = urllib.parse.urljoin(f"{args.endpoint}/", f"{args.job}/")
    print(f"Posting job report back to {url}")
    print(json.dumps(data, indent=4))
    result = requests.put(url, json=data)
    print(f"Report response: {result.status_code}")
    print(result.text)
    result.raise_for_status()


if __name__ == "__main__":
    main()
