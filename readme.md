A crawler for academic confereces. All papers in AAAI, NIPS, ACL, AISTATS and AIIDE from year 2010 to 2016 are crawled. For academic use only.

Install prerequisites:

    pip install -r requirements.txt

Install the project:

    python setup.py develop --user --record files.txt

Uninstall the project:

    cat files.txt | xargs rm -rf

Prepare dataset: (depending on your network status, it will typically take 1-3 hours)

    python confcrawler/util.py

To direct download datasets, run the following commands:

    cd data; ./get_data.sh

Or visit the website: http://web.stanford.edu/~huizi/confdata/

To custom year range of the dataset, edit the year range in `confcrawler/util.py`. 

To add another conference, you will need to add your own crawler in `crawl.py`, and add it to the `ClassDict`.
