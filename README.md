# policy_research - handover
# Road map to run the app and make it work

1) git clone from github repo [https://github.com/GKt0/policy_research]
2) install miniconda3 [https://docs.conda.io/en/latest/miniconda.html]
Open Anaconda Prompt (miniconda3) 
## Create virtual environement
1) Go to project directory thanks to cd command
2) conda crate --name myenvname python=3.10
3) conda activate myenv

It's important to know where your virtual environement is stored so that you know where is your python.exe (python interpreter). It's often in C:\Users\current_user\AppData\Local\conda\conda\envs\myenv\

## Run the app
Still using Anaconda Prompt (miniconda3)
1) Go to app directory thanks to cd command
2) install requirements.txt adapting the following command: C:\Users\Gkto\AppData\Local\conda\conda\envs\myenv\python.exe -m pip install -r requirements.txt
It's calling the python interpretor and then launching the command pip install -r requirements.txt
All the necessary packages to make the app run will be installed.

Now, open vs code.
1) Open the project directory
2) Open a powershell terminal
3) adapt and launch this command: 
& C:/Users/Gkto/AppData/Local/conda/conda/envs/myenv/python.exe c:/TFE/handover/policy_research/app/app.py
Again, it's calling the python interpretor and then, it's executing the app.py from the app directory.

## Adapt the code
1) Create a DeeplAPI account, copy the key and paste it in app.py (line 131)
2) Create a Azure Cognitive Search service on Azure Portal. Copy the key and paste it in app.py (line 208)

## Create index in Azure Cognitve Search (FR)
You'll be using jupyter notebook called from Anaconda Prompt (miniconda). Make sure your virtual env is active.
1) Contact Wouter Travers to get the zip file of the previously extracted data from France (légifrance). The files were to heavy to be pushed on github.
2) Unzip the file inside policy_research/etl/France/
3) Open the notebook FR_2_Transform_Load_AzureCS
4) Find the cells about Load and index inside Azure Cognitive Seach Service
5) Create new cells, copy-paste and adapt the code regarding your service-name and your key to load the "data_origin_prepared.parquet" into the Azure Service
6) On ACS UI, configure a semantic search called "semanticsearchconfig" on fields: article_title, child_text

## Create index in Azure Cognitive Search (PT)
1) The sample is smaller. The data is stored in policy_research/etl/Portugal/pt_sample_updated.parquet
2) Open the notebook PT_full_ETL
3) Find the cells about Load and index inside Azure Cognitive Seach Service
4) Create new cells, copy-paste and adapt the code regarding your service-name and your key to load the "data_origin_prepared.parquet" into the Azure Service
5) On ACS UI, configure a semanctic search "semanticsearchconfig" on fields: article_title, child_text
