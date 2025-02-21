#!/usr/bin/env python
# coding: utf-8

# In[1]:


ngram_length = 3
dstype = 'dbp' 
mname = 'debertaV3'


# In[2]:


from colorama import Fore, Style

import os


# In[3]:


path = f"/home/bhairavi/om/om3/{dstype}/{ngram_length}grams_{mname}/"
os.makedirs(path, exist_ok=True)

print("Directory created or already exists.")
 

file_path = path + f'{dstype}_{ngram_length}keys.csv' 
print(Fore.YELLOW,"csv_filePATH--->",file_path)


filepath_full = path + f'{dstype}_{ngram_length}top5.csv' 
print(Fore.YELLOW,"QUE_filePATH--->",filepath_full)
 
 
 
modelpath = f"/home/bhairavi/om/om5/{dstype}/{mname}_{dstype}"

 

print(Fore.YELLOW,'modelPATH--->',modelpath)
 


# In[4]:


import torch  

torch.cuda.empty_cache()  
import pandas as pd
from datasets import Dataset, DatasetDict, load_metric
from transformers import AutoTokenizer, AutoModelForSequenceClassification, TrainingArguments, Trainer, BertForSequenceClassification, BertTokenizer
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, classification_report
 


# %%
from collections import defaultdict
import string
 
import torch.nn.functional as F
from nltk.util import ngrams

import numpy as np  
  


# In[5]:


# %%
from datasets import load_dataset

dataset = load_dataset("DeveloperOats/DBPedia_Classes", name='default' )


# %%
dataset


# %%
dataset

# %%
train_df = pd.DataFrame(dataset['train'])
test_df = pd.DataFrame(dataset['test'])
validation_df = pd.DataFrame(dataset['validation'])

# %%
train_df['split'] = 'train'

test_df['split'] = 'test'

validation_df['split'] = 'validation'

# %%
df = pd.concat([train_df, test_df, validation_df], ignore_index=True)

# %%
df.shape

# %%
df.columns

# %%
 

# %%
df['l3'].nunique()

# %%


# %%

# %%
df['label'] = df['l3']


# %%

# %%
from sklearn.preprocessing import LabelEncoder

# %%
le = LabelEncoder()
df['target'] = le.fit_transform(df['label'])


# %%

# %%

# %%
df.columns

# %%


# %%
df.shape

# %%


# %%

  
 
 
 

# %%
numlabel = df['target'].nunique()
numlabel


# %%


# %%

# %%
from transformers import AutoTokenizer, AutoModelForSequenceClassification

device = "cuda"  # the device to load the model onto

# Load the tokenizer and model
tokenizer = AutoTokenizer.from_pretrained(modelpath)
model = AutoModelForSequenceClassification.from_pretrained(modelpath, num_labels=numlabel)

# Move the model to the specified device
model.to(device)


# %%


# %%
# df['token_length'] = df['text'].apply(lambda x: len(tokenizer.tokenize(x)))

# # Calculate the maximum token length
# max_length = df['token_length'].max()
# Calculate the token length using the split method
df['token_length'] = df['text'].apply(lambda x: len(x.split()))

# Calculate the maximum token length
max_length = df['token_length'].max()



# %%
max_length

# %%

# Calculate the next maximum token length
next_max_token_length = df['token_length'].nlargest(2).iloc[1] 


# Calculate the average token length
average_token_length = df['token_length'].mean()

# Display the results
print(f"Maximum token length: {max_length}")
print(f"Next maximum token length: {next_max_token_length}") 
print(f"Average token length: {average_token_length:.2f}")

# %%
min(df['token_length'])


# %%

# %%
fdf = df[df['token_length'] == 5]

# %%
fdf

# %%
df = df[df['token_length'] >= 5]

# %%
df.shape
 


# %%
df.columns

# %%
train_df = df[df['split'] == 'train'].drop(columns=['split'])

test_df = df[df['split'] == 'test'].drop(columns=['split'])

val_df = df[df['split'] == 'validation'].drop(columns=['split'])

# %%
train_df.shape, test_df.shape, val_df.shape

# %%

def tokenize_and_format(examples):
    # Tokenize the texts
    tokenized_inputs = tokenizer(examples['text'], padding="max_length", truncation=True, max_length=max_length)
    tokenized_inputs['label'] = list(map(int, examples['target']))
    return tokenized_inputs





# %%
# Convert pandas DataFrame to Hugging Face's Dataset
train_dataset = Dataset.from_pandas(train_df)
eval_dataset = Dataset.from_pandas(val_df) 
test_dataset = Dataset.from_pandas(test_df)

# Map the tokenization function across the datasets
train_dataset = train_dataset.map(tokenize_and_format, batched=True,batch_size=16)
eval_dataset = eval_dataset.map(tokenize_and_format, batched=True,batch_size=16) 
test_dataset = test_dataset.map(tokenize_and_format, batched=True,batch_size=16)




# In[6]:


# %%


# %%
from sklearn.metrics import f1_score, precision_score, recall_score

def compute_metrics(pred):
    labels = pred.label_ids
    preds = pred.predictions.argmax(-1)
    f1 = f1_score(labels, preds, average='weighted')
    precision = precision_score(labels, preds, average='weighted')
    recall = recall_score(labels, preds, average='weighted')
    return {
        'eval_f1': f1,
        'eval_precision': precision,
        'eval_recall': recall,
    }

 

 
 

training_args = TrainingArguments(
    output_dir="./results",
    evaluation_strategy="epoch",  # Use 'epoch' to evaluate at the end of each epoch
    save_strategy="epoch",  # Also use 'epoch' to save at the end of each epoch
    learning_rate=2e-5,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    num_train_epochs=3,
    weight_decay=0.01,
    load_best_model_at_end=True,  # Load the best model at the end of training based on metric
    metric_for_best_model='f1',  # Define the metric for evaluating the best model
    logging_dir='./logs',
    logging_steps=10,
    report_to=[] 
)


 

trainer = Trainer(
    model=model,
    args=training_args ,  # Here you will need to make sure that the Trainer is set up correctly
    compute_metrics=compute_metrics,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    tokenizer=tokenizer
)

 




# In[7]:


io=   pd.DataFrame(eval_dataset)
 
batch_size = 4

# Convert your DataFrame to a list of texts
texts = io['text'].tolist()

# Set the device to GPU if available, otherwise use CPU
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Move model to the specified device
model = model.to(device)
 
model.eval()

# Disable gradient calculations for efficiency
with torch.no_grad():
    # Initialize lists to store predictions
    all_predictions = []
    
    # Process data in batches
    for start in range(0, len(texts), batch_size):
        end = start + batch_size
        batch_texts = texts[start:end]
        
        # Tokenize the batch
        inputs = tokenizer(batch_texts, padding=True, truncation=True, return_tensors="pt", max_length=512)
        
        # Move inputs to the same device as model
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        # Get predictions
        outputs = model(**inputs)
        # Apply softmax to get probabilities from the logits
        probabilities = torch.nn.functional.softmax(outputs.logits, dim=1)
        # Get the predicted class indices
        predicted_indices = torch.argmax(probabilities, dim=1)
        
        # Ensure the indices are back on CPU for DataFrame operations
        predicted_indices = predicted_indices.cpu()
        
        # Convert indices to actual labels if labels are strings
        if hasattr(tokenizer, 'get_labels') and callable(tokenizer.get_labels):
            predicted_labels = [tokenizer.get_labels()[idx] for idx in predicted_indices]
        else:
            predicted_labels = predicted_indices.tolist()
        
        # Append batch predictions to the list
        all_predictions.extend(predicted_labels)


io['predicted_label'] = all_predictions
 


# In[8]:


device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

top_n = 5


# In[9]:


io[f'significant_{ngram_length}grams'] = None
io[f'{ngram_length}gram_weights'] = None 

def occlusion(text, model, tokenizer, label, ngram_length, device):
    inputs = tokenizer(text, return_tensors='pt').to(device)
    original_logits = model(**inputs).logits
    original_probs = F.softmax(original_logits, dim=-1)
    original_prediction = original_probs[0][label].item()
    ngram_importances = defaultdict(float)
    words = text.split()
    ngrams_list = list(ngrams(words, ngram_length))
    for ngram in ngrams_list:
        occluded_text = " ".join([word if word not in ngram else "[OCCLUDED]" for word in words])
        occluded_inputs = tokenizer(occluded_text, return_tensors='pt').to(device)
        occluded_logits = model(**occluded_inputs).logits
        occluded_probs = F.softmax(occluded_logits, dim=-1)
        occluded_prediction = occluded_probs[0][label].item()
        ngram_importances[" ".join(ngram)] = original_prediction - occluded_prediction
        
    return ngram_importances

def aggregate_and_filter_positive_attributions(ngram_attributions, threshold=0):
    significant_ngrams = {
        ngram: value for ngram, value in ngram_attributions.items()
        if value > threshold
    }
    return significant_ngrams

def select_top_ngrams(ngram_importances, top_n=top_n):
    sorted_ngrams = sorted(ngram_importances.items(), key=lambda item: item[1], reverse=True)
    top_ngrams = sorted_ngrams[:top_n]
    return top_ngrams

for index, row in io.iterrows():
    if row['target'] == row['predicted_label']:  
        ngram_attributions = occlusion(row['text'], model, tokenizer, row['label'], ngram_length, device)
        positive_attributions = aggregate_and_filter_positive_attributions(ngram_attributions)
        top_ngrams = select_top_ngrams(positive_attributions, top_n=top_n)  
        io.at[index, f'significant_{ngram_length}grams'] = [ngram for ngram, _ in top_ngrams]  
        io.at[index, f'{ngram_length}gram_weights'] = [weight for _, weight in top_ngrams]  


# In[ ]:


io.to_csv(filepath_full,index= False)

io[0:4]


# In[ ]:


io[f'significant_{ngram_length}grams'][0]


# In[ ]:


# %%

 
io['text'][0], io[f'significant_{ngram_length}grams'][0]



# In[ ]:


# %%

# %%
io['label'] = le.inverse_transform(io['target'])

 


# In[ ]:


# %%
io= io.dropna()

# %%


# In[ ]:


# label_to_words = io.groupby('label')['significant_words'].apply(lambda words: set().union(*words)).to_dict()
label_to_words = io.groupby('label')[f'significant_{ngram_length}grams'].apply(lambda words: set().union(*words)).to_dict()
# label_to_words = io.groupby('label')['significant_5grams'].apply(lambda words: set().union(*words)).to_dict()
 
print(label_to_words)



# In[ ]:


# %%

# %%



label_to_words_and_weights = {}

for label, group in io.groupby('label'):
    word_weights_dict = {}
    for index, row in group.iterrows():
        words = row[f'significant_{ngram_length}grams']
        weights = row[f'{ngram_length}gram_weights']
        for word, weight in zip(words, weights):
            if word in word_weights_dict:
                # Take the maximum of the existing and current weight
                word_weights_dict[word] = max(word_weights_dict[word], weight)
            else:
                word_weights_dict[word] = weight
    label_to_words_and_weights[label] = word_weights_dict

# Display the dictionary with labels, words, and their maximum weights
print(label_to_words_and_weights)


# In[ ]:


# %%


# %%
label_to_words = label_to_words_and_weights

# %%
len(list(label_to_words['Acne']))



# In[ ]:


# %%

# %%
len(label_to_words)



# In[ ]:


# %%

# %%
label_to_words

 


# In[ ]:


test_data = pd.DataFrame(test_dataset)

 

 
from nltk.tokenize import sent_tokenize, word_tokenize

# %%
def split_text(text):
 
    sentences = sent_tokenize(text)  # Tokenize the text into sentences
    third_index = len(sentences) // 2  # Calculate index for one-third
    first_part = ' '.join(sentences[:third_index])  # First third of sentences
    remaining_part = ' '.join(sentences[third_index:])  # Remaining two-thirds
    return first_part, remaining_part
 
# Apply the function to the DataFrame
test_data[['first_half', 'second_half']] = test_data['text'].apply(lambda x: pd.Series(split_text(x)))


# %%
test_data['first_half'][0:4] , test_data['second_half'][0:4]

# %%

 
# %%


# In[ ]:


# %%
tdf = test_data[['first_half', 'label']]
tdf = Dataset.from_pandas(tdf)


 
   
def tokenize_function(examples):
    return tokenizer(examples['first_half'], truncation=True, padding="max_length", max_length=512)

tdf = tdf.map(tokenize_function, batched=True)

# Predict using the trained model
output = trainer.predict(tdf)
predictions = np.argmax(output.predictions, axis=1)
labels = output.label_ids 

# Generate the classification report
report = classification_report(
    labels,
    predictions,
    target_names=np.unique(labels).astype(str),  # Convert labels to string if necessary
    digits=4
)
print(Fore.RED +"first half i.e partial info classification report, baseline 1")
print(report)



# In[ ]:


# Move model to the specified device
model = model.to(device)

# Set the model to evaluation mode
model.eval()

# Disable gradient calculations for efficiency
with torch.no_grad():
    # Assuming your DataFrame `io` has a column 'text' containing the text to predict
    texts = test_data['first_half'].tolist()
    # Tokenize the text
    inputs = tokenizer(texts, padding=True, truncation=True, return_tensors="pt", max_length=512)

    # Move inputs to the same device as model
    inputs = {k: v.to(device) for k, v in inputs.items()}

    # Get predictions
    outputs = model(**inputs)
    # Apply softmax to get probabilities from the logits
    probabilities = torch.nn.functional.softmax(outputs.logits, dim=1)
    # Get the top 3 predicted class indices and their probabilities
    top_probs, top_indices = torch.topk(probabilities, 3, dim=1)

    # Ensure the indices and probabilities are back on CPU for DataFrame operations
    top_indices = top_indices.cpu()
    top_probs = top_probs.cpu()

    # Convert indices to actual labels if labels are strings
    if hasattr(tokenizer, 'get_labels') and callable(tokenizer.get_labels):
        predicted_labels = [[tokenizer.get_labels()[idx] for idx in indices] for indices in top_indices]
    else:
        predicted_labels = top_indices.tolist()

    # Add top 3 predictions to DataFrame
    test_data['top3_predicted_labels'] = predicted_labels
    test_data['top3_predicted_probabilities'] = top_probs.tolist()


 
test_data = test_data[['text','label','target','first_half','second_half','top3_predicted_labels']]

 
 

# %%
test_data['top3_predicted_target']  =  test_data['top3_predicted_labels']

# %%
test_data['label'] = le.inverse_transform(test_data['target'])

# Decode 'top3_predicted_labels' - since these are lists, we apply the inverse transform in a vectorized manner
test_data['top3_predicted_labels'] = test_data['top3_predicted_labels'].apply(lambda x: le.inverse_transform(x))

 

# %%

# %%
def map_significant_words(predictions):
    print(predictions)
    for row in predictions:
        print(row)
    return [label_to_words.get(row, []) for row in predictions]
    # return [[result[pred] for pred in row] for row in predictions]

# Applying the mapping function
test_data['significant_words'] = test_data['top3_predicted_labels'].apply(map_significant_words)

# %%
test_data


# In[ ]:


# %%

# %%
test_data.to_csv(file_path,index= False)


# In[ ]:


# %%
df = test_data

 
df['significant_words'][0]

 


# In[ ]:


# %%
# %%
df.rename(columns={'significant_words': 'significant_words_weights'}, inplace=True)
 


# In[ ]:


# %%
len(df['significant_words_weights'][0])


# In[ ]:


# %%
df['significant_words_weights'][0][0]  

# %%


# In[ ]:


top_n = 15  # The number of top words you want to select

def filter_top_n_words(list_of_dicts):
    processed_list = []
    
    for index, dct in enumerate(list_of_dicts):
        if isinstance(dct, dict):
            # Sort the items by value in descending order
            sorted_items = sorted(dct.items(), key=lambda item: item[1], reverse=True)
            # Select the top N words
            top_items = sorted_items[:top_n]
            # Extract the keys (words) and add them to the list as a set
            processed_list.append(set(key for key, value in top_items))
        else:
            # Print the index and the problematic element
            print(f"Non-dictionary element at index {index}: {dct}")
            # Optionally, add an empty set or handle differently based on your needs
            processed_list.append(set())
    
    return processed_list

# Apply the function to each element in the DataFrame column
df['significant_words'] = df['significant_words_weights'].apply(filter_top_n_words)


# In[ ]:


# %%
df['significant_words'][0][0]  , df['significant_words'][0][1], df['significant_words'][0][2]


# %%


# In[ ]:


# %%
df.shape


# %%


# In[ ]:


df['significant_words'][0][0]  , df['significant_words_weights'][0][0] 



# In[ ]:


# %%
# %%
df = df.dropna(ignore_index =True)


# In[ ]:


# %%
df.to_csv(file_path ,index= False)

# %%
df.columns


# In[ ]:


# %%
len(df['significant_words'][0]),len(df['significant_words'][0][0])

# %

