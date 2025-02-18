import modal
import json
import os
import subprocess
import time

app = modal.App("sync-bitcoin")
volume = modal.Volume.from_name("bitcoin-data")

dockerfile_image = (
    modal.Image.from_dockerfile("./Dockerfile", add_python="3.12", ignore=["*.venv"])
)

@app.function(volumes={"/mnt/data/bitcoin-unique": volume}, image=dockerfile_image)
def run_bitcoind():
    try:
        subprocess.run(["chmod", "-R", "u+w", "/mnt/data/bitcoin-unique"], check=True)
        print("Permissions updated for /mnt/data/bitcoin-unique")

        bitcoind_process = subprocess.Popen(
            ["bitcoind", "-datadir=/mnt/data/bitcoin-unique"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print("bitcoind process started.")

        # Keep reading logs so that the function doesn't exit
        for line in iter(bitcoind_process.stdout.readline, b''):
            print(f"STDOUT: {line.decode().strip()}")
        
        for line in iter(bitcoind_process.stderr.readline, b''):
            print(f"STDERR: {line.decode().strip()}")

        bitcoind_process.wait()  # Wait indefinitely for bitcoind to exit

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
        # Start bitcoind in detached mode
        run_bitcoind.remote()
        print("bitcoind started in detached mode.")

        # Check bitcoind status
        while True:
            try:
                getblock.remote("0000000000000000000000000000000000000000000000000000000000000000")  # Genesis block
                print("bitcoind is ready!")
                break
            except Exception:
                print("bitcoind not yet ready, retrying...")
                time.sleep(10)

        # Keep the app running
        while True:
            print("Modal app running... checking sync progress.")
            time.sleep(300)  # Print status every 5 minutes

    except Exception as e:
        print(f"Error in main function: {e}")