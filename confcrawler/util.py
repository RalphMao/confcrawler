'''
Author: Huizi Mao
Email: ralphmao95 at gmail.com
Date: Sun Oct 16 20:18:52 2016
'''

import pickle
import os

from confcrawler.crawl import ClassDict

class DataManager:
    
    def __init__(self, data_dir, years = range(2008, 2016), inspect=True):
        self.data_dir = data_dir
        self.data = {}
        self.years = years
        self.inspect = inspect

    def get(self, name):
        assert name in ClassDict, "Name %s not found"%name 
        fname = self.data_dir + '/' + name + '-ft.pkl'
        if os.path.exists(fname):
            self.data[name] = pickle.load(open(fname, 'rb'))
        else:
            self.data[name] = {}
        no_years = filter(lambda x:x not in self.data[name], self.years)
        if len(no_years) > 0:
            crawler = ClassDict[name](data_dir=self.data_dir,wait_time=0.5)
            infos = crawler.prepare_dataset(years=no_years)
            self.data[name].update(crawler.get_texts(infos))
            pickle.dump(self.data[name], open(fname, 'wb'))

        return self.data[name]

    def getall(self, year = None):
        for name in ClassDict:
            self.get(name)
        if year is not None:
            data_year = {}
            for name in self.data:
                data_year[name] = self.data[name].get(year, [])
            return data_year
        else:
            return self.data

    def getalldocs(self, year):
        alldocs = []
        ids = []
        if type(year) is list:
            for y in year:
                docs_tmp, ids_tmp, id2names = self.getalldocs(y)
                alldocs.extend(docs_tmp)
                ids.extend(ids_tmp)
        else:
            data = self.getall(year=year)
            id2names = data.keys()
            for idx, name in enumerate(id2names):
                key = 'texts' 
                alldocs.extend(map(lambda x:x[key], data[name]))
                ids.extend([idx] * len(data[name]))
        return alldocs, ids, id2names
        
def main():
    manager = DataManager('./data', inspect = False, years=range(2010, 2017))
    manager.getall()

if __name__ == "__main__":
    main()
