import modal
import json
import os
import subprocess

app = modal.App("sync-bitcoin")
volume = modal.Volume.from_name("bitcoin-data")

dockerfile_image = (
    modal.Image.from_dockerfile("./Dockerfile", add_python="3.12", ignore=["*.venv"])
)

@app.function(volumes={"/mnt/data/bitcoin-unique": volume}, image=dockerfile_image)
def run_bitcoind():
    try:
        # Change permission to override files in /mnt/data/bitcoin-unique
        subprocess.run(["chmod", "-R", "u+w", "/mnt/data/bitcoin-unique"], check=True)
        print("Permissions updated for /mnt/data/bitcoin-unique")

        # Start bitcoind
        bitcoind_process = subprocess.Popen(["bitcoind", "-datadir=/mnt/data/bitcoin-unique"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("bitcoind process started.")

        # Log stdout and stderr
        while True:
            out = bitcoind_process.stdout.readline()
            if out == '' and bitcoind_process.poll() is not None:
                break
            if out:
                print(f"STDOUT: {out.strip()}")
        while True:
            err = bitcoind_process.stderr.readline()
            if err:
                print(f"STDERR: {err.strip()}")
    except Exception as e:
        print(f"Error running bitcoind: {e}")

@app.function(image=dockerfile_image)
def getblock(block_hash: str):
    import requests
    url = "http://127.0.0.1:8332"
    headers = {'content-type': 'text/plain;'}
    data = json.dumps({"method": "getblock", "params": [block_hash], "id": 1})
    try:
        response = requests.post(url, data=data, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        return None

@app.local_entrypoint()
def main():
    try:
        run_bitcoind.remote()
        print("bitcoind started in detached mode.")
        # Example: getblock call after setting up a tunnel (you can uncomment and use when needed)
        # import time
        # time.sleep(10)  # Wait for bitcoind to be fully started
        # block_info = getblock("0000000000000000000d3bd4b2e5f29dc43f1ff9c3d8adbc0c0d08de4d042b4a")
        # print(block_info)
    except Exception as e:
        print(f"Error in main function: {e}")
