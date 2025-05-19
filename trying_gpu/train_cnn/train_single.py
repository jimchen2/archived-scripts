import torch
import torch.nn as nn
import torch.optim as optim
import torchvision
import torchvision.transforms as transforms
import time
import os
import argparse

# --- Model Definition ---
class ConfigurableCNN(nn.Module):
    def __init__(self, num_classes=10, channels_scale=1):
        super(ConfigurableCNN, self).__init__()
        # Adjust channels based on scale_factor
        c1 = int(32 * channels_scale)
        c2 = int(64 * channels_scale)
        c3 = int(128 * channels_scale)
        fc_in_features = int(c3 * 4 * 4)
        fc_hidden = int(512 * channels_scale)

        # Input: 32x32x3
        self.conv_block1 = nn.Sequential(
            nn.Conv2d(3, c1, kernel_size=3, padding=1), # 32x32xc1
            nn.ReLU(),
            nn.Conv2d(c1, c1, kernel_size=3, padding=1),# 32x32xc1
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2),      # 16x16xc1
            nn.Dropout(0.25)
        )
        self.conv_block2 = nn.Sequential(
            nn.Conv2d(c1, c2, kernel_size=3, padding=1),# 16x16xc2
            nn.ReLU(),
            nn.Conv2d(c2, c2, kernel_size=3, padding=1), # 16x16xc2
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2),       # 8x8xc2
            nn.Dropout(0.25)
        )
        self.conv_block3 = nn.Sequential(
            nn.Conv2d(c2, c3, kernel_size=3, padding=1), # 8x8xc3
            nn.ReLU(),
            nn.Conv2d(c3, c3, kernel_size=3, padding=1),# 8x8xc3
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2),        # 4x4xc3
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

def main(args):
    print(f"--- Configuration ---")
    print(f"Epochs: {args.epochs}")
    print(f"Total Batch Size: {args.batch_size}")
    print(f"Learning Rate: {args.lr}")
    print(f"Model Channels Scale: {args.model_scale}")
    print(f"Number of Workers: {args.num_workers}")
    print(f"Requested GPUs: {args.gpus}")
    print("---------------------\n")

    # 1. Setup device
    actual_gpus_used = 0
    if args.gpus > 0 and torch.cuda.is_available():
        if torch.cuda.device_count() < args.gpus:
            print(f"Warning: Requested {args.gpus} GPUs, but only {torch.cuda.device_count()} are available. Using {torch.cuda.device_count()} GPUs.")
            actual_gpus_used = torch.cuda.device_count()
        else:
            actual_gpus_used = args.gpus
        
        if actual_gpus_used > 0:
            device = torch.device("cuda")
            print(f"CUDA is available. Attempting to use {actual_gpus_used} GPU(s).")
            # Ensure specific GPUs are visible if needed (often not necessary if not restricting elsewhere)
            # os.environ["CUDA_VISIBLE_DEVICES"] = ",".join(map(str, range(actual_gpus_used)))
            # print(f"CUDA_VISIBLE_DEVICES set to: {os.environ.get('CUDA_VISIBLE_DEVICES')}")
        else: # Should not happen if args.gpus > 0 and cuda is available, but as a fallback
            device = torch.device("cpu")
            print("CUDA was requested but 0 GPUs ended up being used. Falling back to CPU.")
            actual_gpus_used = 0

    else:
        device = torch.device("cpu")
        print("Using CPU.")
        actual_gpus_used = 0

    # 2. Load and preprocess CIFAR-10 dataset
    print("\nLoading CIFAR-10 dataset...")
    transform_train = transforms.Compose([
        transforms.RandomHorizontalFlip(),
        transforms.RandomCrop(32, padding=4),
        transforms.ToTensor(),
        transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010))
    ])
    transform_test = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010))
    ])

    # Use a subset for faster demonstration if needed, by slicing trainset
    trainset = torchvision.datasets.CIFAR10(root='./data', train=True,
                                            download=True, transform=transform_train)
    trainloader = torch.utils.data.DataLoader(trainset, batch_size=args.batch_size, # This is TOTAL batch size
                                              shuffle=True, num_workers=args.num_workers,
                                              pin_memory=True if device.type == 'cuda' else False)

    # testset = torchvision.datasets.CIFAR10(root='./data', train=False,
    #                                        download=True, transform=transform_test)
    # testloader = torch.utils.data.DataLoader(testset, batch_size=args.batch_size * 2,
    #                                          shuffle=False, num_workers=args.num_workers,
    #                                          pin_memory=True if device.type == 'cuda' else False)
    num_classes = 10

    # 3. Initialize the model
    print("\nBuilding the CNN model...")
    model = ConfigurableCNN(num_classes=num_classes, channels_scale=args.model_scale)

    # 4. Handle device placement and DataParallel
    model.to(device) # Move model to the primary device first

    if device.type == 'cuda' and actual_gpus_used > 1:
        print(f"Wrapping model with nn.DataParallel for {actual_gpus_used} GPUs.")
        # Specify device_ids to use only the 'actual_gpus_used'
        gpu_ids = list(range(actual_gpus_used))
        model = nn.DataParallel(model, device_ids=gpu_ids)
        print(f"DataParallel using GPU IDs: {gpu_ids}")
        print(f"Effective batch size per GPU: {args.batch_size // actual_gpus_used}")
    elif device.type == 'cuda' and actual_gpus_used == 1:
        print(f"Model will run on a single GPU: cuda:{torch.cuda.current_device()}")
        print(f"Effective batch size per GPU: {args.batch_size}")
    else: # CPU
        print("Model will run on CPU.")
        print(f"Effective batch size on CPU: {args.batch_size}")


    total_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Total trainable parameters: {total_params:,}")

    # 5. Define loss function and optimizer
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=args.lr)

    # 6. Train the model (shortened loop for demonstration)
    print(f"\nStarting training for {args.epochs} epochs...")
    start_time = time.time()

    for epoch in range(args.epochs):
        model.train()
        running_loss = 0.0
        epoch_start_time = time.time()

        for i, data in enumerate(trainloader, 0):
            inputs, labels = data
            # DataParallel handles moving parts of the batch to other GPUs from the primary device
            inputs, labels = inputs.to(device), labels.to(device) 

            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            running_loss += loss.item()

            # if (i + 1) % 50 == 0: # Print less frequently for faster runs
            #     print(f'[Epoch {epoch + 1}, Batch {i + 1:4d}/{len(trainloader)}] loss: {loss.item():.3f}')
        
        epoch_time = time.time() - epoch_start_time
        avg_epoch_loss = running_loss / len(trainloader)
        print(f"Epoch {epoch + 1}/{args.epochs} finished. Avg Loss: {avg_epoch_loss:.4f}. Time: {epoch_time:.2f}s")

    total_training_time = time.time() - start_time
    print(f"\nTraining finished in {total_training_time:.2f} seconds.")
    print(f"Average time per epoch: {total_training_time / args.epochs:.2f} seconds.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="PyTorch CIFAR-10 CNN Training")
    parser.add_argument('--epochs', type=int, default=3, help='Number of epochs to train (default: 3)')
    parser.add_argument('--batch_size', type=int, default=256, help='TOTAL input batch size (default: 256)')
    parser.add_argument('--lr', type=float, default=0.001, help='Learning rate (default: 0.001)')
    parser.add_argument('--model_scale', type=float, default=1.0, help='Multiplier for model channel sizes (default: 1.0)')
    parser.add_argument('--gpus', type=int, default=1, help='Number of GPUs to use (0 for CPU, 1 for single GPU, >1 for DataParallel - default: 1)')
    parser.add_argument('--num_workers', type=int, default=2, help='Number of dataloader workers (default: 2)')
    
    # Quick way to set CUDA_VISIBLE_DEVICES if you want to test specific GPUs
    # For example, if you have 4 GPUs and want to test using only GPU 2 and 3 for a 2-GPU test:
    # CUDA_VISIBLE_DEVICES="2,3" python your_script.py --gpus 2
    # PyTorch will then see GPU 2 as cuda:0 and GPU 3 as cuda:1
    # For this script, we'll assume PyTorch sees GPUs starting from 0 up to torch.cuda.device_count()-1

    cli_args = parser.parse_args()
    main(cli_args)