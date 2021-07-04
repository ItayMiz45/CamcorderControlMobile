import torch
import torchvision
import torchvision.transforms as transforms
import matplotlib.pyplot as plt
import numpy as np
import torch.nn as nn
import torch.optim as optim
from Dataset import Dataset
from CNN import Net


CSV_FILE_PATH = r"gestures.csv"
MODEL_PATH = "gestures.pth"

# Set device
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

# Hyperparameters
learning_rate = 1e-4
batch_size = 64
num_epochs = 8
test_size = 294


print(device)


transform = transforms.Compose(
    [transforms.ToTensor(),
     transforms.Resize(32),
     transforms.RandomHorizontalFlip(),
     transforms.RandomErasing(p=0.25, value=0, scale=(0.001, 0.005), ratio=(0.1, 0.2)),
     transforms.RandomErasing(p=0.25, value=1, scale=(0.001, 0.005), ratio=(0.1, 0.2)),
     transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))])

dataset = Dataset(csv_file=CSV_FILE_PATH, root_dir=r"Frames", transform=transform)

train_set, test_set = torch.utils.data.random_split(dataset, [len(dataset)-test_size, test_size])

train_loader = torch.utils.data.DataLoader(dataset=train_set, batch_size=batch_size, shuffle=True)
test_loader = torch.utils.data.DataLoader(dataset=test_set, batch_size=batch_size, shuffle=True)

print(len(train_set), len(test_set))


# functions to show an image
def imshow(img):
    img = img / 2 + 0.5     # unnormalize
    npimg = img.numpy()
    plt.imshow(np.transpose(npimg, (1, 2, 0)))
    plt.show()


net = Net()
net.to(device)

criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(net.parameters(), lr=learning_rate, betas=(0.9, 0.999))


for epoch in range(num_epochs):  # loop over the dataset multiple times

    running_loss = 0.0
    for i, (inputs, labels) in enumerate(train_loader, 0):
        inputs, labels = inputs.to(device), labels.to(device)

        # zero the parameter gradients
        optimizer.zero_grad()

        # forward + backward + optimize
        outputs = net(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        # print statistics
        running_loss += loss.item()
        if i % 20 == 20-1:    # print every 20 mini-batches
            print('[%d, %5d] loss: %.3f' %
                  (epoch + 1, i + 1, running_loss / 20))
            running_loss = 0.0

print('Finished Training')
torch.save(net.state_dict(), MODEL_PATH)


# use custom model
dataiter = iter(test_loader)
images, labels = dataiter.next()
print(labels)

# print images
imshow(torchvision.utils.make_grid(images))
print('GroundTruth: ', ' '.join('%5s' % labels[j].item() for j in range(batch_size)))

outputs = net(images.to(device))

_, predicted = torch.max(outputs, 1)

print('Predicted: ', ' '.join('%5s' % predicted[j].item()
                              for j in range(batch_size)))

correct = 0
total = 0
with torch.no_grad():
    for data in test_loader:
        images, labels = data
        images, labels = images.to(device), labels.to(device)
        outputs = net(images)
        _, predicted = torch.max(outputs.data, 1)
        predicted = predicted.to(device)
        total += labels.size(0)
        correct += (predicted == labels).sum().item()

print(f'Accuracy of the network on the {test_size} test images: %d %%' % (
    100 * correct / total))
