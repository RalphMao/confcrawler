'''
Author: Huizi Mao
Email: ralphmao95 at gmail.com
Date: Sun Oct 16 17:02:35 2016
'''


import colorlog
import requests
import time
import bs4
import os, sys
import traceback
import progressbar
import re

handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter(
    '%(log_color)s%(levelname)s:%(name)s:%(message)s'))
logger = colorlog.getLogger('[%s]'%__file__)
logger.addHandler(handler)
logger.setLevel(15)
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

def get_soup(url):
    content = requests.get(url, verify=False, headers = headers).content
    return bs4.BeautifulSoup(content)

def get_fulltext(url, filename):
    content = requests.get(url, verify=False, headers = headers).content
    with open(filename + '.pdf', 'wb') as f:
        f.write(content)
    flag = os.system('pdftotext %s.pdf %s.txt > /dev/null 2>&1'%(filename, filename))
    if flag == 2:
        raise KeyboardInterrupt
    elif flag == 0:
        return open('%s.txt'%filename).read()
    else:
        return ''

def wmap(wait_time, inspect):
    def map_func(func, iterable, callback=None):
        results = []
        for idx, unit in enumerate(iterable):
            try:
                results.append(func(unit))
            except Exception as e:
                traceback.print_stack()
                print e
                if not inspect:
                    continue
                else:
                    import IPython;IPython.embed()

            time.sleep(wait_time)
            if callback is not None and len(results) > 0:
                callback(results[-1], unit)
        return results
    return map_func

class ConferenceCrawler(object):
    name='CONF'
    def __init__(self, wait_time = 0, data_dir='.', inspect=True):
        self.wmap = wmap(wait_time, inspect)
        self.data_dir = data_dir

    def get_site_by_year(self, year):
        raise Exception('Unimplemented')

    def get_articles_by_site(self, site_url):
        raise Exception('Unimplemented')

    def get_full_details(self, article_url):
        raise Exception('Unimplemented')

    def prepare_dataset(self, years = range(2008,2015)):
        site_urls = self.wmap(self.get_site_by_year, years)
        logger.info('%s Crawler starts!'%self.name)
        logger.info('Got %d sites in total'%len(site_urls))
        def log_site(articles, site_url):
            logger.info('Find %d articles in site %s'%(len(articles), site_url))

        article_sets = self.wmap(self.get_articles_by_site, site_urls, log_site)
        total_number = sum(map(len, article_sets))
        if total_number == 0:
            return dict(zip(years, [[]]*len(years)))
        full_details = []
        logger.info('Get info of all articles')
        bar = progressbar.ProgressBar(maxval=total_number,
            widgets=[progressbar.Bar('=', '[', ']'), ' ', progressbar.ETA()])
        bar.start()
        def log_article(article_info, article_url):
            bar.update(bar.currval+1)

        for article_set in article_sets:
            full_details.append(self.wmap(self.get_full_details, article_set, log_article))

        return dict(zip(years, full_details))

    def get_texts(self, dataset):
        total_num = sum(map(lambda x:dataset[x].__len__(), dataset))
        bar = progressbar.ProgressBar(maxval=total_num,
            widgets=[progressbar.Bar('=', '[', ']'), ' ', progressbar.ETA()])
        bar.start()
        def append_fulltext(article):
            if article.get('texts','') != '':
                return article
            if article.get('pdf_href', '') == '':
                article['texts'] == ''
                return article
            article['texts'] = get_fulltext(article['pdf_href'], self.data_dir + '/tmp')
            return article

        def log_article(article_info, article_url):
            bar.update(bar.currval+1)

        for year in dataset:
            dataset[year] = self.wmap(append_fulltext, dataset[year], log_article)
                
        return dataset

class NIPSCrawler(ConferenceCrawler):
    start_page = 'https://papers.nips.cc'
    name = 'NIPS'
    def __init__(self, *args, **kwargs):
        super(NIPSCrawler, self).__init__(*args, **kwargs)
        self.content = get_soup(self.start_page).findAll(name='li')

    def get_site_by_year(self, year):
        texts = map(lambda x:x.text, self.content)
        id_ = filter(lambda x:str(year) in texts[x], range(len(texts)))[0]
        href = self.content[id_].find('a').get('href')
        return self.start_page + href

    def get_articles_by_site(self, site_url):
        soup = get_soup(site_url)
        articles = soup.findAll('li')
        results = []
        for article in articles:
            hrefs = article.findAll('a')
            if len(hrefs) < 2 :
                continue
            else:
                results.append(self.start_page + hrefs[0].get('href'))
        return results

    def get_full_details(self, article_url):
        soup = get_soup(article_url)
        main_frame = soup.find(*['div'], **{'class':'main wrapper clearfix'})

        title = main_frame.find(*['h2'], **{'class':'subtitle'}).text
        authors_li = main_frame.findAll(*['li'], **{'class':'author'})
        authors = map(lambda x:x.text, authors_li)
        all_hrefs = main_frame.findAll('a')
        pdf_href = self.start_page + filter(lambda x:'[PDF]' in x.text, all_hrefs)[0].get('href')
        abstract = main_frame.find(*['p'], **{'class':'abstract'}).text
        return dict(title=title, authors=authors, abstract=abstract, pdf_href=pdf_href)

class ACLCrawler(ConferenceCrawler):
    name = 'ACL'
    def get_site_by_year(self, year):
        return 'http://aclweb.org/anthology/P/P%02d/'%(year % 100)

    def get_articles_by_site(self, site_url):
        soup = get_soup(site_url)
        ps = soup.findAll('p')[2:]
        results = []
        for p in ps:
            title = p.find('i')
            if title is not None:
                title = title.text
            else:
                continue
            authors = p.find('b')
            if authors is not None:
                authors = authors.text
            else:
                continue
            pdf_href = p.find('a')
            if pdf_href is not None and 'pdf' in pdf_href.get('href'):
                pdf_href = site_url + pdf_href.get('href')
            else:
                continue
            results.append(dict(title=title, authors=authors, abstract='', pdf_href=pdf_href))
        return results

    def get_full_details(self, article):
        return article

class AAAICrawler(ConferenceCrawler):
    start_page = 'http://www.aaai.org/Library/AAAI/'
    name = 'AAAI'
    def __init__(self, *args, **kwargs):
        super(AAAICrawler, self).__init__(*args, **kwargs)

    def get_site_by_year(self, year):
        if year < 2009:
            year = 2009
        return self.start_page + 'aaai%02dcontents.php'%(year % 100)

    def get_articles_by_site(self, site_url):
        soup = get_soup(site_url)
        ps = soup.findAll('p', **{'class':'left'})
        def valid(tag):
            ls = tag.findAll('i')
            if len(ls) != 1: return 0
            if ls[0].text.strip() == 0: return 0
            return 1
        def modify(link):
            parts = link.split('/')
            parts[-2] += 'Paper'
            return '/'.join(parts)
        ps = filter(valid, ps)
        hrefs = map(lambda x:x.find('a').get('href'), ps)
        return map(modify, hrefs)

    def get_full_details(self, article_url):
        soup = get_soup(article_url)
        title = soup.find('div', id='title').text
        authors = soup.find('div', id='author').text
        abstract = soup.find('div', id='abstract').find('div').text
        pdf_href = soup.find('div', id='paper').find('a').get('href')
        def subsititute(link):
            parts = link.split('/')
            parts[-3] = 'download'
            return '/'.join(parts)
        pdf_href = subsititute(pdf_href)
        ''' # for year before 2009
        title = soup.find('h1').text
        pdf_href = self.start_page + soup.find('h1').find('a').get('href')
        ps = soup.findAll('p')
        authors = ps[0].text
        abstract = ps[1].text
        '''
        return dict(title=title, authors=authors, abstract=abstract, pdf_href=pdf_href)

class AISTATSCrawler(ConferenceCrawler):
    name = 'AISTATS'
    start_page = 'http://www.jmlr.org/proceedings/papers/'
    year_vol_map = {2009:5, 2010:9, 2011:15, 2012:22, 2013:31, 2014:33, 2015:38, 2016:51}
    def __init__(self, *args, **kwargs):
        super(AISTATSCrawler, self).__init__(*args, **kwargs)

    def get_site_by_year(self, year):
        return self.start_page + 'v%d/'%(self.year_vol_map.get(year, 0))

    def get_articles_by_site(self, site_url):
        soup = get_soup(site_url)
        infos = []
        if int(re.findall(r'[0-9]+', site_url)[0]) < 31:
            articles = soup.findAll('dl')
            for article in articles:
                title = article.find('dt').text
                authors = article.find('b').text
                hrefs = article.findAll('a')
                abstract_href = filter(lambda x:'abs' in x.text, hrefs)
                pdf_href = filter(lambda x:'pdf' in x.text, hrefs)
                if len(abstract_href) > 0 and len(pdf_href) > 0:
                    infos.append((title, authors, site_url + abstract_href[0].get('href'),
                        site_url + pdf_href[0].get('href')))
        else:
            articles = soup.findAll('div', **{'class':'paper'})
            for article in articles:
                title = article.find('p', **{'class':'title'}).text
                authors = article.find('span', **{'class':'authors'}).text
                hrefs = article.findAll('a')
                abstract_href = filter(lambda x:'abs' in x.text, hrefs)
                pdf_href = filter(lambda x:'pdf' in x.text, hrefs)
                if len(abstract_href) > 0 and len(pdf_href) > 0:
                    infos.append((title, authors, site_url + abstract_href[0].get('href'),
                        site_url + pdf_href[0].get('href')))

        return infos

    def get_full_details(self, article_url):
        soup = get_soup(article_url[2])
        abstract = soup.find('div', id='abstract')
        if abstract is None:
            abstract_ = soup.findAll('p')
            max_len = max(map(lambda x:len(x.text), abstract_))
            abstract = filter(lambda x:len(x.text) == max_len, abstract_)[0]
        abstract = abstract.text
        return dict(title=article_url[0], authors=article_url[1], abstract=abstract, pdf_href=article_url[3])

class AIIDECrawler(AAAICrawler):
    start_page = 'http://www.aaai.org/Library/AIIDE/'
    name = 'AIIDE'
    def get_site_by_year(self, year):
        if year < 2010:
            year = 2000
        return self.start_page + 'aiide%02dcontents.php'%(year % 100)


ClassDict = {
'NIPS':NIPSCrawler,
'AAAI':AAAICrawler,
'AISTATS':AISTATSCrawler,
'AIIDE':AIIDECrawler,
'ACL':ACLCrawler,
}

def main():
    pass 
if __name__ == "__main__":
    main()

