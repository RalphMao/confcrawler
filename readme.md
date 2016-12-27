Install prerequisites:

    pip install -r requirements.txt

Install the project:

    python setup.py develop --user --record files.txt

Uninstall the project:

    cat files.txt | xargs rm -rf

Prepare dataset: (depending on your network status, it will typically take 1-3 hours)

    python confcrawler/util.py

Direct download datasets:

    cd data; ./get_data.sh

To custom year range of the dataset, edit the year range in `confcrawler/util.py`. 

To add another conference, you will need to add your own crawler in `crawl.py`, and add it to the `ClassDict`.
