## Utility Commands

`sudo apt update && sudo apt install ubuntu-drivers-common && sudo ubuntu-drivers autoinstall`

Then reboot

Python:

`sudo apt install python3-pip python3.12-venv python-is-python3 && python3 -m venv ~/.venv`

Activating env: `source ~/.venv/bin/activate`

`pip install torch torchvision ray`

`pip install "ray[train]"`

## 1 VPS

```
root@localhost:~# nvidia-smi
Sat May 17 07:48:43 2025
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 570.133.07             Driver Version: 570.133.07     CUDA Version: 12.8     |
|-----------------------------------------+------------------------+----------------------+
| GPU  Name                 Persistence-M | Bus-Id          Disp.A | Volatile Uncorr. ECC |
| Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
|                                         |                        |               MIG M. |
|=========================================+========================+======================|
|   0  NVIDIA RTX 4000 Ada Gene...    Off |   00000000:00:02.0 Off |                  Off |
| 30%   36C    P8              7W /  130W |       2MiB /  20475MiB |      0%      Default |
|                                         |                        |                  N/A |
+-----------------------------------------+------------------------+----------------------+
|   1  NVIDIA RTX 4000 Ada Gene...    Off |   00000000:00:03.0 Off |                  Off |
| 30%   38C    P8              5W /  130W |       2MiB /  20475MiB |      0%      Default |
|                                         |                        |                  N/A |
+-----------------------------------------+------------------------+----------------------+
```

## `train_single.py`

```
(.venv) root@localhost:~# python train.py --gpus 2 --epochs 10
--- Configuration ---
Epochs: 10
Total Batch Size: 256
Learning Rate: 0.001
Model Channels Scale: 1.0
Number of Workers: 2
Requested GPUs: 2
---------------------

CUDA is available. Attempting to use 2 GPU(s).

Loading CIFAR-10 dataset...

Building the CNN model...
Wrapping model with nn.DataParallel for 2 GPUs.
DataParallel using GPU IDs: [0, 1]
Effective batch size per GPU: 128
Total trainable parameters: 1,341,226

Starting training for 10 epochs...
Epoch 1/10 finished. Avg Loss: 1.8414. Time: 4.77s
Epoch 2/10 finished. Avg Loss: 1.4777. Time: 4.23s
Epoch 3/10 finished. Avg Loss: 1.2875. Time: 4.26s
Epoch 4/10 finished. Avg Loss: 1.1561. Time: 4.15s
Epoch 5/10 finished. Avg Loss: 1.0752. Time: 4.01s
Epoch 6/10 finished. Avg Loss: 0.9815. Time: 4.11s
Epoch 7/10 finished. Avg Loss: 0.9257. Time: 4.49s
Epoch 8/10 finished. Avg Loss: 0.8806. Time: 4.10s
Epoch 9/10 finished. Avg Loss: 0.8403. Time: 4.10s
Epoch 10/10 finished. Avg Loss: 0.8048. Time: 4.47s

Training finished in 42.68 seconds.
Average time per epoch: 4.27 seconds.
(.venv) root@localhost:~# python train.py --gpus  1 --epochs 10
--- Configuration ---
Epochs: 10
Total Batch Size: 256
Learning Rate: 0.001
Model Channels Scale: 1.0
Number of Workers: 2
Requested GPUs: 1
---------------------

CUDA is available. Attempting to use 1 GPU(s).

Loading CIFAR-10 dataset...

Building the CNN model...
Model will run on a single GPU: cuda:0
Effective batch size per GPU: 256
Total trainable parameters: 1,341,226

Starting training for 10 epochs...
Epoch 1/10 finished. Avg Loss: 1.8551. Time: 4.24s
Epoch 2/10 finished. Avg Loss: 1.4865. Time: 4.08s
Epoch 3/10 finished. Avg Loss: 1.3044. Time: 3.86s
Epoch 4/10 finished. Avg Loss: 1.1684. Time: 4.18s
Epoch 5/10 finished. Avg Loss: 1.0739. Time: 3.77s
Epoch 6/10 finished. Avg Loss: 0.9921. Time: 3.78s
Epoch 7/10 finished. Avg Loss: 0.9361. Time: 3.71s
Epoch 8/10 finished. Avg Loss: 0.8894. Time: 4.06s
Epoch 9/10 finished. Avg Loss: 0.8462. Time: 4.11s
Epoch 10/10 finished. Avg Loss: 0.8063. Time: 3.74s

Training finished in 39.53 seconds.
Average time per epoch: 3.95 seconds.
(.venv) root@localhost:~#
```

## `train_ddp.py`

```
(.venv) root@localhost:~# torchrun --standalone --nproc_per_node=1 train_ddp.py --epochs 10 --batch_size 256 --model_scale 0.5
--- PyTorch/CUDA/NCCL Info ---
PyTorch version: 2.7.0+cu126
CUDA available: True
CUDA version: 12.6
Number of GPUs visible to PyTorch: 2
CUDNN available: True
CUDNN version: 90501
NCCL available for distributed: True
NCCL version (from torch.cuda.nccl): (2, 26, 2)
------------------------------

--- DDP Configuration ---
Using 1 GPU(s) for DDP training.
Global Rank: 0, Local Rank: 0, World Size: 1
-------------------------

--- Training Configuration ---
Epochs: 10
Global Batch Size: 256
Learning Rate: 0.001
Model Channels Scale: 0.5
Dataloader Workers per Process: 2
----------------------------

Effective batch size per GPU/process: 256
Process 0 on device: cuda:0

Loading CIFAR-10 dataset (rank 0 ensures download)...
[rank0]:[W517 08:37:08.068871151 ProcessGroupNCCL.cpp:4715] [PG ID 0 PG GUID 0 Rank 0]  using GPU 0 as device used by this process is currently unknown. This can potentially cause a hang if this rank to GPU mapping is incorrect. You can pecify device_id in init_process_group() to force use of a particular device.

Building the CNN model...
Total trainable parameters (DDP model): 337,050

Starting DDP training for 10 epochs...
Epoch 1/10 finished. Global Avg Loss: 1.9651. Time: 4.10s
Epoch 2/10 finished. Global Avg Loss: 1.6876. Time: 3.91s
Epoch 3/10 finished. Global Avg Loss: 1.5409. Time: 3.89s
Epoch 4/10 finished. Global Avg Loss: 1.4496. Time: 3.92s
Epoch 5/10 finished. Global Avg Loss: 1.3769. Time: 3.72s
Epoch 6/10 finished. Global Avg Loss: 1.3301. Time: 3.87s
Epoch 7/10 finished. Global Avg Loss: 1.2793. Time: 3.81s
Epoch 8/10 finished. Global Avg Loss: 1.2361. Time: 3.76s
Epoch 9/10 finished. Global Avg Loss: 1.1923. Time: 3.83s
Epoch 10/10 finished. Global Avg Loss: 1.1634. Time: 3.91s

Training finished in 38.72 seconds.
Average time per epoch: 3.87 seconds.
(.venv) root@localhost:~# torchrun --standalone --nproc_per_node=2 train_ddp.py --epochs 10 --batch_size 256 --model_scale 0.5
W0517 08:38:04.188000 27318 torch/distributed/run.py:766]
W0517 08:38:04.188000 27318 torch/distributed/run.py:766] *****************************************
W0517 08:38:04.188000 27318 torch/distributed/run.py:766] Setting OMP_NUM_THREADS environment variable for each process to be 1 in default, to avoid your system being overloaded, please further tune the variable for optimal performance in your application as needed.
W0517 08:38:04.188000 27318 torch/distributed/run.py:766] *****************************************
--- PyTorch/CUDA/NCCL Info ---
PyTorch version: 2.7.0+cu126
CUDA available: True
CUDA version: 12.6
Number of GPUs visible to PyTorch: 2
CUDNN available: True
CUDNN version: 90501
NCCL available for distributed: True
NCCL version (from torch.cuda.nccl): (2, 26, 2)
------------------------------

--- DDP Configuration ---
Using 2 GPU(s) for DDP training.
Global Rank: 0, Local Rank: 0, World Size: 2
-------------------------

--- Training Configuration ---
Epochs: 10
Global Batch Size: 256
Learning Rate: 0.001
Model Channels Scale: 0.5
Dataloader Workers per Process: 2
----------------------------

Effective batch size per GPU/process: 128
Process 0 on device: cuda:0

Loading CIFAR-10 dataset (rank 0 ensures download)...
[rank1]:[W517 08:38:06.581472218 ProcessGroupNCCL.cpp:4715] [PG ID 0 PG GUID 0 Rank 1]  using GPU 1 as device used by this process is currently unknown. This can potentially cause a hang if this rank to GPU mapping is incorrect. You can pecify device_id in init_process_group() to force use of a particular device.
[rank0]:[W517 08:38:07.767833946 ProcessGroupNCCL.cpp:4715] [PG ID 0 PG GUID 0 Rank 0]  using GPU 0 as device used by this process is currently unknown. This can potentially cause a hang if this rank to GPU mapping is incorrect. You can pecify device_id in init_process_group() to force use of a particular device.

Building the CNN model...
Total trainable parameters (DDP model): 337,050

Starting DDP training for 10 epochs...
Epoch 1/10 finished. Global Avg Loss: 1.9544. Time: 3.28s
Epoch 2/10 finished. Global Avg Loss: 1.6330. Time: 2.90s
Epoch 3/10 finished. Global Avg Loss: 1.4857. Time: 2.94s
Epoch 4/10 finished. Global Avg Loss: 1.4019. Time: 2.90s
Epoch 5/10 finished. Global Avg Loss: 1.3197. Time: 3.05s
Epoch 6/10 finished. Global Avg Loss: 1.2604. Time: 3.04s
Epoch 7/10 finished. Global Avg Loss: 1.2017. Time: 2.87s
Epoch 8/10 finished. Global Avg Loss: 1.1534. Time: 2.93s
Epoch 9/10 finished. Global Avg Loss: 1.1171. Time: 2.70s
Epoch 10/10 finished. Global Avg Loss: 1.0823. Time: 3.15s

Training finished in 29.75 seconds.
Average time per epoch: 2.98 seconds.
(.venv) root@localhost:~#
```

## `train_ray.py`

Open 2 VPS in the same VPC

For VPS `10.0.0.2`

```
user@fedora ~/Downloads> ssh root@172.234.237.235
root@172.234.237.235's password:
Welcome to Ubuntu 24.04.2 LTS (GNU/Linux 6.8.0-53-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/pro

 System information as of Sat May 17 09:58:43 AM UTC 2025

  System load:  0.11               Processes:             149
  Usage of /:   0.4% of 503.43GB   Users logged in:       1
  Memory usage: 1%                 IPv4 address for eth0: 10.0.0.2
  Swap usage:   0%


The list of available updates is more than a week old.
To check for new updates run: sudo apt update

Last login: Sat May 17 09:57:31 2025 from 112.29.110.68
root@localhost:~# ping 10.0.0.3
PING 10.0.0.3 (10.0.0.3) 56(84) bytes of data.
64 bytes from 10.0.0.3: icmp_seq=1 ttl=62 time=0.578 ms
64 bytes from 10.0.0.3: icmp_seq=2 ttl=62 time=0.787 ms
^C
--- 10.0.0.3 ping statistics ---
2 packets transmitted, 2 received, 0% packet loss, time 1032ms
rtt min/avg/max/mdev = 0.578/0.682/0.787/0.104 ms
root@localhost:~# nvidia-smi
Sat May 17 10:11:34 2025
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 570.133.07             Driver Version: 570.133.07     CUDA Version: 12.8     |
|-----------------------------------------+------------------------+----------------------+
| GPU  Name                 Persistence-M | Bus-Id          Disp.A | Volatile Uncorr. ECC |
| Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
|                                         |                        |               MIG M. |
|=========================================+========================+======================|
|   0  NVIDIA RTX 4000 Ada Gene...    Off |   00000000:00:02.0 Off |                  Off |
| 30%   29C    P8              7W /  130W |       2MiB /  20475MiB |      0%      Default |
|                                         |                        |                  N/A |
+-----------------------------------------+------------------------+----------------------+
```

For the other VPS `10.0.0.3`

```
root@localhost:~# ping 10.0.0.2
PING 10.0.0.2 (10.0.0.2) 56(84) bytes of data.
64 bytes from 10.0.0.2: icmp_seq=1 ttl=62 time=0.501 ms
64 bytes from 10.0.0.2: icmp_seq=2 ttl=62 time=0.779 ms
root@localhost:~# nvidia-smi
Sat May 17 10:12:39 2025
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 570.133.07             Driver Version: 570.133.07     CUDA Version: 12.8     |
|-----------------------------------------+------------------------+----------------------+
| GPU  Name                 Persistence-M | Bus-Id          Disp.A | Volatile Uncorr. ECC |
| Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
|                                         |                        |               MIG M. |
|=========================================+========================+======================|
|   0  NVIDIA RTX 4000 Ada Gene...    Off |   00000000:00:02.0 Off |                  Off |
| 30%   31C    P8              4W /  130W |       2MiB /  20475MiB |      0%      Default |
|                                         |                        |                  N/A |
+-----------------------------------------+------------------------+----------------------+
|   1  NVIDIA RTX 4000 Ada Gene...    Off |   00000000:00:03.0 Off |                  Off |
| 30%   32C    P8              4W /  130W |       2MiB /  20475MiB |      0%      Default |
|                                         |                        |                  N/A |
+-----------------------------------------+------------------------+----------------------+
```

On VPS `10.0.0.2` (HEAD node)

```
(.venv) root@localhost:~# ray start --head --port=6379 --dashboard-host=0.0.0.0 --num-gpus=1
Enable usage stats collection? This prompt will auto-proceed in 10 seconds to avoid blocking cluster startup. Confirm [Y/n]: y
Usage stats collection is enabled. To disable this, add `--disable-usage-stats` to the command that starts the cluster, or run the following command: `ray disable-usage-stats` before starting the cluster. See https://docs.ray.io/en/master/cluster/usage-stats.html for more details.

Local node IP: 10.0.0.2

--------------------
Ray runtime started.
--------------------
```

On VPS `10.0.0.3`

```
(.venv) root@localhost:~# ray start --address='10.0.0.2:6379' --num-gpus=2
Local node IP: 10.0.0.3
[2025-05-17 10:16:45,866 W 1126 1126] global_state_accessor.cc:435: Retrying to get node with node ID e620c543aebb3ebc722de83213907bc24cb984043ad8b24449b74411
[2025-05-17 10:16:46,868 W 1126 1126] global_state_accessor.cc:435: Retrying to get node with node ID e620c543aebb3ebc722de83213907bc24cb984043ad8b24449b74411

--------------------
Ray runtime started.
--------------------
```

On HEAD (`10.0.0.2`)

```
python train_ray.py \
    --epochs 5 \
    --batch_size 384 \
    --lr 0.001 \
    --model_scale 1.0 \
    --num_dataloader_workers 2 \
    --num_workers 3 \
    --gpus_per_worker 1
```
