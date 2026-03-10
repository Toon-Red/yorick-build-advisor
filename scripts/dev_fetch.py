"""Fetch and run dev builds from GitHub Actions artifacts.

Usage:
    python scripts/dev_fetch.py                  # List recent dev builds
    python scripts/dev_fetch.py --branch feat-x  # Filter by branch
    python scripts/dev_fetch.py --run 12345      # Download specific run
    python scripts/dev_fetch.py --latest          # Download latest dev build
    python scripts/dev_fetch.py --run 12345 --launch  # Download and launch

Requires: gh CLI (https://cli.github.com/) authenticated.
"""

import argparse
import json
import os
import subprocess
import sys
import zipfile

REPO = "Toon-Red/yorick-build-advisor"
DEV_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dev-builds")


def gh(*args):
    """Run a gh CLI command and return stdout."""
    cmd = ["gh"] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"gh error: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    return result.stdout.strip()


def list_runs(branch=None, limit=10):
    """List recent dev-build workflow runs."""
    args = ["run", "list", "-R", REPO, "-w", "Dev Build", "--json",
            "databaseId,headBranch,headSha,status,conclusion,createdAt,displayTitle",
            "-L", str(limit)]
    if branch:
        args += ["-b", branch]
    raw = gh(*args)
    runs = json.loads(raw) if raw else []
    return runs


def list_artifacts(run_id):
    """List artifacts for a specific run."""
    raw = gh("api", f"repos/{REPO}/actions/runs/{run_id}/artifacts")
    data = json.loads(raw)
    return data.get("artifacts", [])


def download_artifact(run_id, launch=False):
    """Download the dev exe artifact from a run."""
    os.makedirs(DEV_DIR, exist_ok=True)

    artifacts = list_artifacts(run_id)
    dev_arts = [a for a in artifacts if a["name"].startswith("YorickBuildAdvisor-dev")]
    if not dev_arts:
        print(f"No dev artifact found for run {run_id}")
        return None

    art = dev_arts[0]
    art_name = art["name"]
    zip_path = os.path.join(DEV_DIR, f"{art_name}.zip")
    exe_path = os.path.join(DEV_DIR, f"{art_name}.exe")

    if os.path.exists(exe_path):
        print(f"Already downloaded: {exe_path}")
    else:
        print(f"Downloading artifact: {art_name} ...")
        gh("run", "download", str(run_id), "-R", REPO, "-n", art_name, "-D", DEV_DIR)

        # gh downloads to DEV_DIR/YorickBuildAdvisor.exe — rename it
        downloaded = os.path.join(DEV_DIR, "YorickBuildAdvisor.exe")
        if os.path.exists(downloaded):
            os.rename(downloaded, exe_path)
            print(f"Saved: {exe_path}")
        else:
            print(f"Download completed but exe not found at expected path")
            return None

    if launch:
        print(f"Launching: {exe_path}")
        subprocess.Popen([exe_path], creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)

    return exe_path


def main():
    parser = argparse.ArgumentParser(description="Fetch dev builds from GitHub Actions")
    parser.add_argument("--branch", "-b", help="Filter by branch name")
    parser.add_argument("--run", "-r", type=int, help="Download artifact from specific run ID")
    parser.add_argument("--latest", action="store_true", help="Download the latest successful dev build")
    parser.add_argument("--launch", action="store_true", help="Launch the exe after downloading")
    parser.add_argument("--limit", "-n", type=int, default=10, help="Number of runs to list")
    args = parser.parse_args()

    if args.run:
        download_artifact(args.run, launch=args.launch)
        return

    runs = list_runs(branch=args.branch, limit=args.limit)
    if not runs:
        print("No dev builds found.")
        return

    if args.latest:
        # Find first successful run
        for run in runs:
            if run["conclusion"] == "success":
                print(f"Latest successful: run #{run['databaseId']} on {run['headBranch']} ({run['headSha'][:7]})")
                download_artifact(run["databaseId"], launch=args.launch)
                return
        print("No successful dev builds found.")
        return

    # List mode
    print(f"{'RUN ID':<12} {'BRANCH':<25} {'SHA':<9} {'STATUS':<12} {'DATE'}")
    print("-" * 80)
    for run in runs:
        status = run["conclusion"] or run["status"]
        sha = run["headSha"][:7]
        date = run["createdAt"][:10]
        branch = run["headBranch"][:24]
        print(f"{run['databaseId']:<12} {branch:<25} {sha:<9} {status:<12} {date}")
    print(f"\nTo download: python scripts/dev_fetch.py --run <RUN_ID>")
    print(f"To download & launch: python scripts/dev_fetch.py --run <RUN_ID> --launch")


if __name__ == "__main__":
    main()
