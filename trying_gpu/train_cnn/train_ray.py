import time
import os
import argparse
import ray
from ray import train
from ray.train import ScalingConfig, RunConfig
from ray.train.torch import TorchTrainer, TorchConfig
from ray.util.placement_group import placement_group

def train_loop_per_worker(config):
    import torch
    import torch.nn as nn
    import torch.optim as optim
    import torchvision
    import torchvision.transforms as transforms

    # Debug GPU assignment
    world_rank = train.get_context().get_world_rank()
    world_size = train.get_context().get_world_size()
    node_id = train.get_context().get_node_id()
    local_rank = train.get_context().get_local_rank()
    
    # Print GPU information
    cuda_visible = os.environ.get("CUDA_VISIBLE_DEVICES", "Not set")
    num_gpus = torch.cuda.device_count()
    gpu_name = torch.cuda.get_device_name(0) if num_gpus > 0 else "No GPU"
    print(f"Worker {world_rank} (local_rank={local_rank}, node_id={node_id}): "
          f"CUDA_VISIBLE_DEVICES={cuda_visible}, "
          f"Num GPUs={num_gpus}, "
          f"GPU Name={gpu_name}, "
          f"Device=cuda:{local_rank}")

    # Set device
    device = torch.device(f"cuda:{local_rank}" if torch.cuda.is_available() else "cpu")
    torch.cuda.set_device(device)

    class ConfigurableCNN(nn.Module):
        def __init__(self, num_classes=10, channels_scale=1):
            super(ConfigurableCNN, self).__init__()
            c1 = int(32 * channels_scale)
            c2 = int(64 * channels_scale)
            c3 = int(128 * channels_scale)
            fc_in_features = int(c3 * 4 * 4)
            fc_hidden = int(512 * channels_scale)
            self.conv_block1 = nn.Sequential(
                nn.Conv2d(3, c1, kernel_size=3, padding=1),
                nn.ReLU(),
                nn.Conv2d(c1, c1, kernel_size=3, padding=1),
                nn.ReLU(),
                nn.MaxPool2d(kernel_size=2, stride=2),
                nn.Dropout(0.25)
            )
            self.conv_block2 = nn.Sequential(
                nn.Conv2d(c1, c2, kernel_size=3, padding=1),
                nn.ReLU(),
                nn.Conv2d(c2, c2, kernel_size=3, padding=1),
                nn.ReLU(),
                nn.MaxPool2d(kernel_size=2, stride=2),
                nn.Dropout(0.25)
            )
            self.conv_block3 = nn.Sequential(
                nn.Conv2d(c2, c3, kernel_size=3, padding=1),
                nn.ReLU(),
                nn.Conv2d(c3, c3, kernel_size=3, padding=1),
                nn.ReLU(),
                nn.MaxPool2d(kernel_size=2, stride=2),
                nn.Dropout(0.25)
            )
            self.flatten = nn.Flatten()
            self.fc_block = nn.Sequential(
                nn.Linear(fc_in_features, fc_hidden),
                nn.ReLU(),
                nn.Dropout(0.5),
                nn.Linear(fc_hidden, num_classes)
            )

        def forward(self, x):
            x = self.conv_block1(x)
            x = self.conv_block2(x)
            x = self.conv_block3(x)
            x = self.flatten(x)
            x = self.fc_block(x)
            return x

    lr = config["lr"]
    epochs = config["epochs"]
    batch_size_per_worker = config["batch_size_per_worker"]
    model_scale = config["model_scale"]
    num_workers_dataloader = config["num_workers_dataloader"]

    if world_rank == 0:
        print(f"--- PyTorch/CUDA/NCCL Info (from worker 0) ---")
        print(f"PyTorch version: {torch.__version__}")
        print(f"CUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"CUDA version: {torch.version.cuda}")
            print(f"Number of GPUs visible to PyTorch in this worker: {torch.cuda.device_count()}")
            print(f"CUDNN available: {torch.backends.cudnn.is_available()}")
            print(f"CUDNN version: {torch.backends.cudnn.version()}")
        print("------------------------------\n")

        print(f"--- Ray Train Configuration (from worker 0) ---")
        print(f"Using {world_size} GPU(s) for Ray Train training.")
        print(f"Worker Rank: {world_rank}, World Size: {world_size}")
        print(f"Device for this worker: {device}")
        print("-------------------------\n")

        print(f"--- Training Configuration (from worker 0) ---")
        print(f"Epochs: {epochs}")
        print(f"Global Batch Size (calculated): {batch_size_per_worker * world_size}")
        print(f"Batch Size per Worker: {batch_size_per_worker}")
        print(f"Learning Rate: {lr}")
        print(f"Model Channels Scale: {model_scale}")
        print(f"Dataloader Workers per Ray Worker: {num_workers_dataloader}")
        print("----------------------------\n")

    print(f"Worker {world_rank}: Loading CIFAR-10 dataset...")
    transform_train = transforms.Compose([
        transforms.RandomHorizontalFlip(),
        transforms.RandomCrop(32, padding=4),
        transforms.ToTensor(),
        transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010))
    ])
    trainset = torchvision.datasets.CIFAR10(root='./data', train=True,
                                            download=True, transform=transform_train)
    testset = torchvision.datasets.CIFAR10(root='./data', train=False,
                                           download=True, transform=transform_train)

    trainloader = torch.utils.data.DataLoader(trainset, batch_size=batch_size_per_worker,
                                              shuffle=True,
                                              num_workers=num_workers_dataloader,
                                              pin_memory=True)
    
    trainloader = train.torch.prepare_data_loader(trainloader)

    num_classes = 10

    if world_rank == 0:
        print("\nBuilding the CNN model...")
    model = ConfigurableCNN(num_classes=num_classes, channels_scale=model_scale)
    model = train.torch.prepare_model(model)

    if world_rank == 0:
        total_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
        print(f"Total trainable parameters (DDP-wrapped model on worker 0): {total_params:,}")

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)
    
    if world_rank == 0:
        print(f"\nStarting Ray Train training for {epochs} epochs...")
    
    overall_start_time_worker = time.time()

    for epoch in range(epochs):
        model.train()
        running_loss_sum_worker = 0.0
        num_samples_processed_worker = 0
        epoch_start_time_worker = time.time()

        for i, data in enumerate(trainloader):
            inputs, labels = data
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            running_loss_sum_worker += loss.item() * inputs.size(0)
            num_samples_processed_worker += inputs.size(0)
        
        epoch_time_worker = time.time() - epoch_start_time_worker
        avg_loss_epoch_worker = running_loss_sum_worker / num_samples_processed_worker if num_samples_processed_worker > 0 else 0.0
        
        train.report({
            "epoch": epoch + 1,
            "loss": avg_loss_epoch_worker,
            "epoch_time_worker": epoch_time_worker,
            "lr": optimizer.param_groups[0]['lr']
        })
        
        if world_rank == 0:
            print(f"Worker 0: Epoch {epoch + 1}/{epochs} finished. Avg Loss (worker 0 shard): {avg_loss_epoch_worker:.4f}. Time: {epoch_time_worker:.2f}s")

    if world_rank == 0:
        total_training_time_worker = time.time() - overall_start_time_worker
        print(f"\nWorker 0 training loop finished in {total_training_time_worker:.2f} seconds.")
        print(f"Worker 0 average time per epoch: {total_training_time_worker / epochs:.2f} seconds.")

def main(args):
    if not ray.is_initialized():
        ray.init(address='auto', ignore_reinit_error=True)
    
    num_total_workers = args.num_workers
    
    if args.batch_size % num_total_workers != 0:
        print(f"Warning: Global batch size {args.batch_size} is not divisible by total workers {num_total_workers}. "
              "This may lead to uneven batch distribution. Consider adjusting.")
    
    batch_size_per_worker = args.batch_size // num_total_workers
    if batch_size_per_worker == 0:
        raise ValueError(f"Global batch size {args.batch_size} is too small for {num_total_workers} workers. Batch size per worker would be 0.")

    print(f"\n--- Ray Train Job Configuration ---")
    print(f"Total workers (GPUs): {num_total_workers}")
    print(f"GPUs per worker: {args.gpus_per_worker}")
    print(f"Global batch size: {args.batch_size}")
    print(f"Effective batch size per worker: {batch_size_per_worker}")
    if ray.is_initialized():
        print(f"Head node Ray address for workers to connect: {ray.get_runtime_context().gcs_address}")
    else:
        print(f"Head node Ray address for workers to connect: (Ray not initialized at this print)")
    print("---------------------------------\n")

    # Create a placement group for strict GPU assignment
    bundles = [{"GPU": args.gpus_per_worker, "CPU": 1} for _ in range(num_total_workers)]
    pg = placement_group(bundles, strategy="STRICT_SPREAD")
    ray.get(pg.ready())  # Wait for placement group to be ready

    scaling_config = ScalingConfig(
        num_workers=num_total_workers,
        use_gpu=True,
        resources_per_worker={"GPU": args.gpus_per_worker, "CPU": 1},
        placement_group=pg
    )

    train_loop_config = {
        "lr": args.lr,
        "epochs": args.epochs,
        "batch_size_per_worker": batch_size_per_worker,
        "model_scale": args.model_scale,
        "num_workers_dataloader": args.num_dataloader_workers
    }

    torch_config = TorchConfig(backend="nccl")

    run_config = RunConfig(
        name=f"cifar10_configurable_cnn_scale{args.model_scale}_bs{args.batch_size}_lr{args.lr}",
        verbose=2,
    )

    trainer = TorchTrainer(
        train_loop_per_worker=train_loop_per_worker,
        train_loop_config=train_loop_config,
        scaling_config=scaling_config,
        torch_config=torch_config,
        run_config=run_config
    )

    print("Starting Ray TorchTrainer fit...")
    start_time_trainer_fit = time.time()
    result = trainer.fit()
    end_time_trainer_fit = time.time()

    print(f"\n--- Ray Train Job Summary ---")
    print(f"Training finished. Total time for trainer.fit(): {end_time_trainer_fit - start_time_trainer_fit:.2f} seconds.")
    print(f"Last reported metrics:\n{result.metrics}")
    if result.checkpoint:
        print(f"Last checkpoint saved at: {result.checkpoint.path}")
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Ray Train CIFAR-10 CNN Training")
    parser.add_argument('--epochs', type=int, default=3, help='Number of epochs to train')
    parser.add_argument('--batch_size', type=int, default=256, help='TOTAL input batch size across all GPUs/workers')
    parser.add_argument('--lr', type=float, default=0.001, help='Learning rate')
    parser.add_argument('--model_scale', type=float, default=1.0, help='Multiplier for model channel sizes')
    parser.add_argument('--num_dataloader_workers', type=int, default=2, help='Number of dataloader workers per Ray worker process')
    parser.add_argument('--num_workers', type=int, default=None, help='Total number of Ray workers (GPUs) to use for training. If None, uses all available GPUs in the cluster.')
    parser.add_argument('--gpus_per_worker', type=int, default=1, help='Number of GPUs to assign to each Ray worker. Typically 1 for DDP-style training.')

    cli_args = parser.parse_args()

    _ray_initialized_for_gpu_check = False
    if cli_args.num_workers is None:
        if not ray.is_initialized():
            ray.init(ignore_reinit_error=True)
            _ray_initialized_for_gpu_check = True
        available_gpus = int(ray.cluster_resources().get("GPU", 0))
        if available_gpus == 0:
            if _ray_initialized_for_gpu_check and ray.is_initialized():
                ray.shutdown()
            raise ValueError("No GPUs available in the Ray cluster and --num_workers not specified. Cannot run GPU training.")
        cli_args.num_workers = available_gpus
        print(f"Auto-detected {available_gpus} GPUs. Setting --num_workers to {cli_args.num_workers}.")
        if _ray_initialized_for_gpu_check and ray.is_initialized():
            ray.shutdown()
            _ray_initialized_for_gpu_check = False

    if cli_args.gpus_per_worker != 1:
        print("Warning: For DDP-style training with PyTorch, `gpus_per_worker` is typically 1. "
              "Each worker process handles one GPU. If you have a different setup in mind, ensure it's intentional.")

    try:
        main(cli_args)
    finally:
        if ray.is_initialized():
            ray.shutdown()