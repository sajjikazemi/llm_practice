import os
import random
from dotenv import load_dotenv
from huggingface_hub import login
from datasets import load_dataset, Dataset, DatasetDict
from items import Item
from loaders import ItemLoader
import matplotlib.pyplot as plt
from collections import Counter, defaultdict
import numpy as np
import pickle

load_dotenv()
os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY', 'your-key-if-not-using-env')
os.environ['ANTHROPIC_API_KEY'] = os.getenv('ANTHROPIC_API_KEY', 'your-key-if-not-using-env')
os.environ['HF_TOKEN'] = os.getenv('HF_TOKEN', 'your-key-if-not-using-env')

hf_token = os.environ['HF_TOKEN']
login(hf_token, add_to_git_credential=True)

items = ItemLoader("Appliances").load()

#print(items[1].prompt)

dataset_names = [
    "Automotive",
    "Electronics",
    "Office_Products",
    "Tools_and_Home_Improvement",
    "Cell_Phones_and_Accessories",
    "Toys_and_Games",
    "Appliances",
    "Musical_Instruments",
]

items = []
for dataset_name in dataset_names:
    loader = ItemLoader(dataset_name)
    items.extend(loader.load())

print(f"A grand total of {len(items):,} items")

# # Plot the distribution of token counts again
# tokens = [item.token_count for item in items]
# plt.figure(figsize=(15, 6))
# plt.title(f"Token counts: Avg {sum(tokens)/len(tokens):,.1f} and highest {max(tokens):,}\n")
# plt.xlabel('Length (tokens)')
# plt.ylabel('Count')
# plt.hist(tokens, rwidth=0.7, color="skyblue", bins=range(0, 300, 10))
# plt.show()

# # Plot the distribution of prices
# prices = [item.price for item in items]
# plt.figure(figsize=(15, 6))
# plt.title(f"Prices: Avg {sum(prices)/len(prices):,.1f} and highest {max(prices):,}\n")
# plt.xlabel('Price ($)')
# plt.ylabel('Count')
# plt.hist(prices, rwidth=0.7, color="blueviolet", bins=range(0, 1000, 10))
# plt.show()

# category_counts = Counter()
# for item in items:
#     category_counts[item.category]+=1

# categories = category_counts.keys()
# counts = [category_counts[category] for category in categories]

# # Bar chart by category
# plt.figure(figsize=(15, 6))
# plt.bar(categories, counts, color="goldenrod")
# plt.title('How many in each category')
# plt.xlabel('Categories')
# plt.ylabel('Count')

# plt.xticks(rotation=30, ha='right')

# # Add value labels on top of each bar
# for i, v in enumerate(counts):
#     plt.text(i, v, f"{v:,}", ha='center', va='bottom')

# # Display the chart
# plt.show()

# Balancing the dataset
slots = defaultdict(list)
for item in items:
    slots[round(item.price)].append(item)

np.random.seed(42)
random.seed(42)
sample = []
for i in range(1, 1000):
    slot = slots[i]
    if i>=240:
        sample.extend(slot)
    elif len(slot) <= 1200:
        sample.extend(slot)
    else:
        weights = np.array([1 if item.category=='Automotive' else 5 for item in slot])
        weights = weights / np.sum(weights)
        selected_indices = np.random.choice(len(slot), size=1200, replace=False, p=weights)
        selected = [slot[i] for i in selected_indices]
        sample.extend(selected)

print(f"There are {len(sample):,} items in the sample")

# # Plot the distribution of prices in sample
# prices = [float(item.price) for item in sample]
# plt.figure(figsize=(15, 10))
# plt.title(f"Avg {sum(prices)/len(prices):.2f} and highest {max(prices):,.2f}\n")
# plt.xlabel('Price ($)')
# plt.ylabel('Count')
# plt.hist(prices, rwidth=0.7, color="darkblue", bins=range(0, 1000, 10))
# plt.show()

# # Categories distributions
# category_counts = Counter()
# for item in sample:
#     category_counts[item.category]+=1

# categories = category_counts.keys()
# counts = [category_counts[category] for category in categories]

# # Create bar chart
# plt.figure(figsize=(15, 6))
# plt.bar(categories, counts, color="lightgreen")

# # Customize the chart
# plt.title('How many in each category')
# plt.xlabel('Categories')
# plt.ylabel('Count')

# plt.xticks(rotation=30, ha='right')

# # Add value labels on top of each bar
# for i, v in enumerate(counts):
#     plt.text(i, v, f"{v:,}", ha='center', va='bottom')

# # Display the chart
# plt.show()

# Dividing the data into train and test sets
random.seed(42)
random.shuffle(sample)
train = sample[:400_000]
test = sample[400_000:402_000]
print(f"Divided into a training set of {len(train):,} items and test set of {len(test):,} items")

# print(train[0].prompt)
# print(test[0].test_prompt())

# Uploading the dataset
train_prompts = [item.prompt for item in train]
train_prices = [item.price for item in train]
test_prompts = [item.test_prompt() for item in test]
test_prices = [item.price for item in test]

train_dataset = Dataset.from_dict({"text": train_prompts, "price": train_prices})
test_dataset = Dataset.from_dict({"text": test_prompts, "price": test_prices})
dataset = DatasetDict({
    "train": train_dataset,
    "test": test_dataset
})

# Push the dataset to the hub
HF_USER = "sajjikazemi"
DATASET_NAME = f"{HF_USER}/pricer-data"
dataset.push_to_hub(DATASET_NAME, private=True)

# Pickle the dataset such that we don't have to execute this code again
with open('train.pkl', 'wb') as file:
    pickle.dump(train, file)

with open('test.pkl', 'wb') as file:
    pickle.dump(test, file)