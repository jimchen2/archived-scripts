```bash
sudo apt update && sudo apt install ubuntu-drivers-common && sudo ubuntu-drivers autoinstall
sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
sudo apt-get update
sudo apt-get install -y docker-ce
sudo systemctl start docker
sudo systemctl enable docker
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
    && curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
```

```bash
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

Verify:

```
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

```
docker run -it --gpus all --net=host --shm-size=32768m bytepsimage/pytorch bash
```

Inside the Docker container's bash shell.

```bash
# now you are in docker environment
export NVIDIA_VISIBLE_DEVICES=0,1,2,3  # Use the GPUs you want (e.g., 0 or 0,1 if you have 2 GPUs)
                                        # Make sure these GPU IDs exist on your system (check with nvidia-smi on host)

export DMLC_WORKER_ID=0                # Your worker ID (0 for the first/only worker)
export DMLC_NUM_WORKER=1               # Total number of workers (1 for a single machine benchmark)
export DMLC_ROLE=worker                # Role is 'worker'

# The following values are placeholders for a single-worker setup but are expected by bpslaunch
export DMLC_NUM_SERVER=1               # Number of parameter servers (1 is fine for this setup)
export DMLC_PS_ROOT_URI=127.0.0.1      # Parameter server IP (use 127.0.0.1 for local)
export DMLC_PS_ROOT_PORT=1234          # Parameter server port (any free port)
```

**Inside the Docker Container: Run the Benchmark**

- `bpslaunch` is a utility from BytePS to launch the training script.

## GPU

```
root@VM-0-3-ubuntu:/# nvidia-smi
Sun May 18 09:51:00 2025
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 570.133.07             Driver Version: 570.133.07     CUDA Version: 12.8     |
|-----------------------------------------+------------------------+----------------------+
| GPU  Name                 Persistence-M | Bus-Id          Disp.A | Volatile Uncorr. ECC |
| Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
|                                         |                        |               MIG M. |
|=========================================+========================+======================|
|   0  Tesla V100-SXM2-32GB           Off |   00000000:00:08.0 Off |                    0 |
| N/A   43C    P0             59W /  300W |       0MiB /  32768MiB |      0%      Default |
|                                         |                        |                  N/A |
+-----------------------------------------+------------------------+----------------------+
|   1  Tesla V100-SXM2-32GB           Off |   00000000:00:09.0 Off |                    0 |
| N/A   41C    P0             55W /  300W |       0MiB /  32768MiB |      0%      Default |
|                                         |                        |                  N/A |
+-----------------------------------------+------------------------+----------------------+
|   2  Tesla V100-SXM2-32GB           Off |   00000000:00:0A.0 Off |                    0 |
| N/A   41C    P0             57W /  300W |       0MiB /  32768MiB |      0%      Default |
|                                         |                        |                  N/A |
+-----------------------------------------+------------------------+----------------------+
|   3  Tesla V100-SXM2-32GB           Off |   00000000:00:0B.0 Off |                    0 |
| N/A   43C    P0             58W /  300W |       0MiB /  32768MiB |      0%      Default |
|                                         |                        |                  N/A |
+-----------------------------------------+------------------------+----------------------+

+-----------------------------------------------------------------------------------------+
| Processes:                                                                              |
|  GPU   GI   CI              PID   Type   Process name                        GPU Memory |
|        ID   ID                                                               Usage      |
|=========================================================================================|
|  No running processes found                                                             |
+-----------------------------------------------------------------------------------------+
```

```
root@VM-0-3-ubuntu:/# bpslaunch python3 /usr/local/byteps/example/pytorch/benchmark_byteps.py --model resnet50 --num-iters 1
BytePS launching worker
Model: resnet50
Batch size: 32
Number of GPUs: 4
Running warmup...
Running benchmark...
Iter #0: 302.7 img/sec per GPU
Img/sec per GPU: 302.7 +-0.0
Total img/sec on 4 GPU(s): 1210.8 +-0.0
```

```
root@VM-0-3-ubuntu:/# bpslaunch python3 /usr/local/byteps/example/pytorch/benchmark_byteps.py --model resnet50 --batch-size 32 --num-iters 20
BytePS launching worker
Model: resnet50
Batch size: 32
Number of GPUs: 4
Running warmup...
Running benchmark...
Iter #0: 303.3 img/sec per GPU
Iter #1: 302.2 img/sec per GPU
Iter #2: 302.1 img/sec per GPU
Iter #3: 302.1 img/sec per GPU
Iter #4: 301.9 img/sec per GPU
Iter #5: 302.0 img/sec per GPU
Iter #6: 301.5 img/sec per GPU
Iter #7: 301.5 img/sec per GPU
Iter #8: 301.1 img/sec per GPU
Iter #9: 300.7 img/sec per GPU
Iter #10: 301.5 img/sec per GPU
Iter #11: 302.4 img/sec per GPU
Iter #12: 301.6 img/sec per GPU
Iter #13: 301.6 img/sec per GPU
Iter #14: 301.5 img/sec per GPU
Iter #15: 302.0 img/sec per GPU
Iter #16: 301.9 img/sec per GPU
Iter #17: 301.7 img/sec per GPU
Iter #18: 301.9 img/sec per GPU
Iter #19: 302.2 img/sec per GPU
Img/sec per GPU: 301.8 +-1.0
Total img/sec on 4 GPU(s): 1207.3 +-4.0
root@VM-0-3-ubuntu:/# bpslaunch python3 /usr/local/byteps/example/pytorch/benchmark_byteps.py --model resnet50 --batch-size 64 --num-iters 20
BytePS launching worker
Model: resnet50
Batch size: 64
Number of GPUs: 4
Running warmup...
Running benchmark...
Iter #0: 329.8 img/sec per GPU
Iter #1: 329.3 img/sec per GPU
Iter #2: 329.0 img/sec per GPU
Iter #3: 329.0 img/sec per GPU
Iter #4: 329.5 img/sec per GPU
Iter #5: 329.5 img/sec per GPU
Iter #6: 329.6 img/sec per GPU
Iter #7: 329.5 img/sec per GPU
Iter #8: 328.4 img/sec per GPU
Iter #9: 329.0 img/sec per GPU
Iter #10: 329.1 img/sec per GPU
Iter #11: 329.1 img/sec per GPU
Iter #12: 329.1 img/sec per GPU
Iter #13: 329.2 img/sec per GPU
Iter #14: 328.6 img/sec per GPU
Iter #15: 329.4 img/sec per GPU
Iter #16: 328.9 img/sec per GPU
Iter #17: 329.3 img/sec per GPU
Iter #18: 329.2 img/sec per GPU
Iter #19: 329.1 img/sec per GPU
Img/sec per GPU: 329.2 +-0.6
Total img/sec on 4 GPU(s): 1316.7 +-2.5
root@VM-0-3-ubuntu:/# bpslaunch python3 /usr/local/byteps/example/pytorch/benchmark_byteps.py --model vgg16 --batch-size 32 --num-iters 20
BytePS launching worker
Model: vgg16
Batch size: 32
Number of GPUs: 4
Running warmup...
Running benchmark...
Iter #0: 212.7 img/sec per GPU
Iter #1: 212.4 img/sec per GPU
Iter #2: 212.3 img/sec per GPU
Iter #3: 212.5 img/sec per GPU
Iter #4: 211.6 img/sec per GPU
Iter #5: 212.5 img/sec per GPU
Iter #6: 212.3 img/sec per GPU
Iter #7: 212.2 img/sec per GPU
Iter #8: 212.4 img/sec per GPU
Iter #9: 212.5 img/sec per GPU
Iter #10: 212.3 img/sec per GPU
Iter #11: 212.4 img/sec per GPU
Iter #12: 212.8 img/sec per GPU
Iter #13: 213.0 img/sec per GPU
Iter #14: 212.4 img/sec per GPU
Iter #15: 212.7 img/sec per GPU
Iter #16: 212.1 img/sec per GPU
Iter #17: 212.3 img/sec per GPU
Iter #18: 212.0 img/sec per GPU
Iter #19: 211.9 img/sec per GPU
Img/sec per GPU: 212.4 +-0.6
Total img/sec on 4 GPU(s): 849.4 +-2.4
root@VM-0-3-ubuntu:/# bpslaunch python3 /usr/local/byteps/example/pytorch/benchmark_byteps.py --model resnet101 --batch-size 32 --num-iters 20
BytePS launching worker
Model: resnet101
Batch size: 32
Number of GPUs: 4
Running warmup...
Running benchmark...
Iter #0: 184.0 img/sec per GPU
Iter #1: 184.9 img/sec per GPU
Iter #2: 183.3 img/sec per GPU
Iter #3: 183.6 img/sec per GPU
Iter #4: 184.0 img/sec per GPU
Iter #5: 184.5 img/sec per GPU
Iter #6: 184.6 img/sec per GPU
Iter #7: 185.1 img/sec per GPU
Iter #8: 185.1 img/sec per GPU
Iter #9: 185.1 img/sec per GPU
Iter #10: 184.2 img/sec per GPU
Iter #11: 184.7 img/sec per GPU
Iter #12: 184.2 img/sec per GPU
Iter #13: 184.7 img/sec per GPU
Iter #14: 184.7 img/sec per GPU
Iter #15: 185.1 img/sec per GPU
Iter #16: 184.1 img/sec per GPU
Iter #17: 184.3 img/sec per GPU
Iter #18: 183.7 img/sec per GPU
Iter #19: 184.7 img/sec per GPU
Img/sec per GPU: 184.4 +-1.0
Total img/sec on 4 GPU(s): 737.7 +-4.1
```

```
root@VM-0-3-ubuntu:/usr/local/byteps/example/pytorch# bpslaunch python3 /usr/local/byteps/example/pytorch/benchmark_cross_barrier_byteps.py --model resnet50 --batch-size 32 --num-iters 20
BytePS launching worker

09:59:30.932 cross_barrier.py:48 INFO: CrossBarrier is enabled.
09:59:30.950 cross_barrier.py:48 INFO: CrossBarrier is enabled.
09:59:30.987 cross_barrier.py:48 INFO: CrossBarrier is enabled.
09:59:31.346 cross_barrier.py:48 INFO: CrossBarrier is enabled.
Model: resnet50
Batch size: 32
Number of GPUs: 4
Running warmup...
Running benchmark...
Iter #0: 253.9 img/sec per GPU
Iter #1: 254.1 img/sec per GPU
Iter #2: 255.9 img/sec per GPU
Iter #3: 225.2 img/sec per GPU
Iter #4: 263.3 img/sec per GPU
Iter #5: 223.6 img/sec per GPU
Iter #6: 259.8 img/sec per GPU
Iter #7: 265.5 img/sec per GPU
Iter #8: 268.7 img/sec per GPU
Iter #9: 228.7 img/sec per GPU
Iter #10: 258.3 img/sec per GPU
Iter #11: 260.8 img/sec per GPU
Iter #12: 261.7 img/sec per GPU
Iter #13: 271.0 img/sec per GPU
Iter #14: 283.7 img/sec per GPU
Iter #15: 265.5 img/sec per GPU
Iter #16: 253.7 img/sec per GPU
Iter #17: 235.6 img/sec per GPU
Iter #18: 288.1 img/sec per GPU
10:00:05.041 cross_barrier.py:88 INFO: training finished!
10:00:05.041 cross_barrier.py:88 INFO: training finished!
10:00:05.041 cross_barrier.py:88 INFO: training finished!
10:00:05.041 cross_barrier.py:88 INFO: training finished!
Iter #19: 271.9 img/sec per GPU
Img/sec per GPU: 257.4 +-33.6
Total img/sec on 4 GPU(s): 1029.8 +-134.3
root@VM-0-3-ubuntu:/usr/local/byteps/example/pytorch# bpslaunch python3 /usr/local/byteps/example/pytorch/benchmark_cross_barrier_byteps.py --model resnet50 --batch-size 64 --fp16 --num-iters 20
BytePS launching worker
10:00:14.286 cross_barrier.py:48 INFO: CrossBarrier is enabled.
10:00:14.323 cross_barrier.py:48 INFO: CrossBarrier is enabled.
10:00:14.342 cross_barrier.py:48 INFO: CrossBarrier is enabled.
10:00:14.862 cross_barrier.py:48 INFO: CrossBarrier is enabled.
Model: resnet50
Batch size: 64
Number of GPUs: 4
Running warmup...
Running benchmark...
Iter #0: 335.0 img/sec per GPU
Iter #1: 278.2 img/sec per GPU
Iter #2: 307.6 img/sec per GPU
Iter #3: 321.7 img/sec per GPU
Iter #4: 324.8 img/sec per GPU
Iter #5: 328.1 img/sec per GPU
Iter #6: 316.6 img/sec per GPU
Iter #7: 326.7 img/sec per GPU
Iter #8: 320.8 img/sec per GPU
Iter #9: 320.4 img/sec per GPU
Iter #10: 318.9 img/sec per GPU
Iter #11: 327.2 img/sec per GPU
Iter #12: 324.0 img/sec per GPU
Iter #13: 318.0 img/sec per GPU
Iter #14: 321.7 img/sec per GPU
Iter #15: 323.3 img/sec per GPU
Iter #16: 315.9 img/sec per GPU
Iter #17: 324.2 img/sec per GPU
Iter #18: 328.1 img/sec per GPU
10:01:06.700 cross_barrier.py:88 INFO: training finished!
10:01:06.700 cross_barrier.py:88 INFO: training finished!
10:01:06.700 cross_barrier.py:88 INFO: training finished!
10:01:06.700 cross_barrier.py:88 INFO: training finished!
Iter #19: 325.5 img/sec per GPU
Img/sec per GPU: 320.3 +-21.9
Total img/sec on 4 GPU(s): 1281.3 +-87.5
root@VM-0-3-ubuntu:/usr/local/byteps/example/pytorch# bpslaunch python3 /usr/local/byteps/example/pytorch/benchmark_cross_barrier_byteps.py --model resnet101 --batch-size 32 --num-iters 20
BytePS launching worker
10:01:16.338 cross_barrier.py:48 INFO: CrossBarrier is enabled.
10:01:16.453 cross_barrier.py:48 INFO: CrossBarrier is enabled.
10:01:16.879 cross_barrier.py:48 INFO: CrossBarrier is enabled.
10:01:16.889 cross_barrier.py:48 INFO: CrossBarrier is enabled.
Model: resnet101
Batch size: 32
Number of GPUs: 4
Running warmup...
Running benchmark...
Iter #0: 116.8 img/sec per GPU
Iter #1: 116.1 img/sec per GPU
Iter #2: 118.7 img/sec per GPU
Iter #3: 120.6 img/sec per GPU
Iter #4: 118.5 img/sec per GPU
Iter #5: 120.7 img/sec per GPU
Iter #6: 119.9 img/sec per GPU
Iter #7: 112.7 img/sec per GPU
Iter #8: 108.5 img/sec per GPU
Iter #9: 115.4 img/sec per GPU
Iter #10: 109.1 img/sec per GPU
Iter #11: 118.6 img/sec per GPU
Iter #12: 112.9 img/sec per GPU
Iter #13: 126.3 img/sec per GPU
Iter #14: 116.9 img/sec per GPU
Iter #15: 117.7 img/sec per GPU
Iter #16: 104.1 img/sec per GPU
Iter #17: 109.9 img/sec per GPU
Iter #18: 101.0 img/sec per GPU
10:02:21.374 cross_barrier.py:88 INFO: training finished!
10:02:21.374 cross_barrier.py:88 INFO: training finished!
10:02:21.374 cross_barrier.py:88 INFO: training finished!
Iter #19: 109.8 img/sec per GPU
Img/sec per GPU: 114.7 +-11.8
Total img/sec on 4 GPU(s): 458.8 +-47.2
10:02:21.376 cross_barrier.py:88 INFO: training finished
```
