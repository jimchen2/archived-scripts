# train_ddp.py
import torch
import torch.nn as nn
import torch.optim as optim
import torchvision
import torchvision.transforms as transforms
import time
import os
import argparse
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel as DDP
from torch.utils.data.distributed import DistributedSampler

# --- Model Definition (Identical to original) ---
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

def setup_ddp():
    """Initializes DDP."""
    dist.init_process_group(backend="nccl", init_method="env://")
    local_rank = int(os.environ['LOCAL_RANK'])
    torch.cuda.set_device(local_rank)
    return local_rank, int(os.environ['RANK']), int(os.environ['WORLD_SIZE'])

def cleanup_ddp():
    """Cleans up DDP."""
    dist.destroy_process_group()

def main(args):
    local_rank, global_rank, world_size = setup_ddp()
    device = torch.device(f"cuda:{local_rank}")

    if global_rank == 0:
        print(f"--- PyTorch/CUDA/NCCL Info ---")
        print(f"PyTorch version: {torch.__version__}")
        print(f"CUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"CUDA version: {torch.version.cuda}")
            print(f"Number of GPUs visible to PyTorch: {torch.cuda.device_count()}") # Should match world_size for DDP
            print(f"CUDNN available: {torch.backends.cudnn.is_available()}")
            print(f"CUDNN version: {torch.backends.cudnn.version()}")
        print(f"NCCL available for distributed: {dist.is_nccl_available()}")
        if dist.is_nccl_available() and hasattr(torch.cuda.nccl, 'version'):
            print(f"NCCL version (from torch.cuda.nccl): {torch.cuda.nccl.version()}")
        print("------------------------------\n")

        print(f"--- DDP Configuration ---")
        print(f"Using {world_size} GPU(s) for DDP training.")
        print(f"Global Rank: {global_rank}, Local Rank: {local_rank}, World Size: {world_size}")
        print("-------------------------\n")

        print(f"--- Training Configuration ---")
        print(f"Epochs: {args.epochs}")
        print(f"Global Batch Size: {args.batch_size}")
        print(f"Learning Rate: {args.lr}")
        print(f"Model Channels Scale: {args.model_scale}")
        print(f"Dataloader Workers per Process: {args.num_workers}")
        print("----------------------------\n")

    if args.batch_size % world_size != 0:
        if global_rank == 0:
            print(f"Warning: Global batch size {args.batch_size} is not divisible by world size {world_size}. "
                  "This may lead to uneven batch distribution. Consider adjusting.")
    per_process_batch_size = args.batch_size // world_size

    if global_rank == 0:
        print(f"Effective batch size per GPU/process: {per_process_batch_size}")
        print(f"Process {global_rank} on device: {device}") # For verification
    # else: # Optional: print device for all ranks to confirm setup
    #     print(f"Process {global_rank} on device: {device}")


    # 2. Load and preprocess CIFAR-10 dataset
    if global_rank == 0:
        print("\nLoading CIFAR-10 dataset (rank 0 ensures download)...")
        # Let rank 0 download, others will use cached
        _ = torchvision.datasets.CIFAR10(root='./data', train=True, download=True)
        _ = torchvision.datasets.CIFAR10(root='./data', train=False, download=True)
    
    dist.barrier() # Ensure dataset is downloaded/prepared before other ranks proceed

    transform_train = transforms.Compose([
        transforms.RandomHorizontalFlip(),
        transforms.RandomCrop(32, padding=4),
        transforms.ToTensor(),
        transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010))
    ])
    # transform_test = transforms.Compose([ ... ]) # if needed

    trainset = torchvision.datasets.CIFAR10(root='./data', train=True,
                                            download=False, transform=transform_train) # download=False now

    train_sampler = DistributedSampler(trainset, num_replicas=world_size, rank=global_rank, shuffle=True)
    
    trainloader = torch.utils.data.DataLoader(trainset, batch_size=per_process_batch_size,
                                              sampler=train_sampler, num_workers=args.num_workers,
                                              pin_memory=True) # shuffle must be False with sampler

    num_classes = 10

    # 3. Initialize the model
    if global_rank == 0:
        print("\nBuilding the CNN model...")
    model = ConfigurableCNN(num_classes=num_classes, channels_scale=args.model_scale).to(device)
    
    # Wrap model with DDP
    model = DDP(model, device_ids=[local_rank], output_device=local_rank, find_unused_parameters=False) # Set find_unused_parameters if your model has them

    if global_rank == 0:
        total_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
        print(f"Total trainable parameters (DDP model): {total_params:,}")

    # 5. Define loss function and optimizer
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=args.lr) # DDP handles gradients for all parameters

    # 6. Train the model
    if global_rank == 0:
        print(f"\nStarting DDP training for {args.epochs} epochs...")
    
    overall_start_time = time.time()

    for epoch in range(args.epochs):
        model.train()
        train_sampler.set_epoch(epoch) # Important for shuffling with DistributedSampler
        
        running_loss_sum_process = 0.0 # Sum of losses for this process
        num_batches_process = 0
        epoch_start_time = time.time()

        for i, data in enumerate(trainloader):
            inputs, labels = data
            inputs, labels = inputs.to(device), labels.to(device)

            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward() # DDP handles gradient synchronization
            optimizer.step()
            
            running_loss_sum_process += loss.item() * inputs.size(0) # loss.item() is avg loss for batch
            num_batches_process += 1
            
            # Optional: Per-batch logging (can be verbose)
            # if global_rank == 0 and (i + 1) % 50 == 0:
            #     print(f'[Epoch {epoch + 1}, Batch {i + 1:4d}/{len(trainloader)}] local loss: {loss.item():.3f}')
        
        epoch_time = time.time() - epoch_start_time
        
        # Calculate average loss for this process's shard
        avg_loss_process = running_loss_sum_process / len(train_sampler) if len(train_sampler) > 0 else 0.0
        
        # Gather and average losses across all processes
        loss_tensor = torch.tensor([avg_loss_process], device=device)
        dist.all_reduce(loss_tensor, op=dist.ReduceOp.AVG) # Average the per-process average losses
        global_avg_epoch_loss = loss_tensor.item()

        if global_rank == 0:
            print(f"Epoch {epoch + 1}/{args.epochs} finished. Global Avg Loss: {global_avg_epoch_loss:.4f}. Time: {epoch_time:.2f}s")

    if global_rank == 0:
        total_training_time = time.time() - overall_start_time
        print(f"\nTraining finished in {total_training_time:.2f} seconds.")
        print(f"Average time per epoch: {total_training_time / args.epochs:.2f} seconds.")

    cleanup_ddp()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="PyTorch CIFAR-10 CNN DDP Training")
    parser.add_argument('--epochs', type=int, default=3, help='Number of epochs to train (default: 3)')
    parser.add_argument('--batch_size', type=int, default=256, help='TOTAL input batch size across all GPUs (default: 256)')
    parser.add_argument('--lr', type=float, default=0.001, help='Learning rate (default: 0.001)')
    parser.add_argument('--model_scale', type=float, default=1.0, help='Multiplier for model channel sizes (default: 1.0)')
    parser.add_argument('--num_workers', type=int, default=2, help='Number of dataloader workers per DDP process (default: 2)')
    
    cli_args = parser.parse_args()
    main(cli_args)