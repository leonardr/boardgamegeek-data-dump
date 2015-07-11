from pdb import set_trace
from bs4 import BeautifulSoup
from dateutil.parser import parse as parse2
import time

def parse(date):
    datetime = parse2(date)
    return time.mktime(datetime.timetuple())

class Scraper(object):

    def contents_string(self, tag):
        if tag is None:
            return None
        value = tag.string
        if value is None:
            # It's more than one string
            value = "\n".join(unicode(x).strip() for x in tag.contents)
        else:
            value = value.strip()
        return value

    def get_tag_value(self, soup, name):
        tag = soup.find(name)
        s = tag.string
        if not s:
            return None
        return s.strip()

    def get_from_soup(self, soup, attribute):
        value = None
        value_tag = getattr(soup, attribute, None)
        if value_tag is not None:
            value = self.contents_string(value_tag)
            value_tag.extract()
            return value

    def get_date_from_soup(self, soup, attribute):
        value = self.get_from_soup(soup, attribute)
        if value is None:
            return value
        return parse(value)

    def set_from_soup(self, soup, attribute):
        value = self.get_from_soup(soup, attribute)
        setattr(self, attribute, value)

    def get_number_from_soup(self, soup, attribute):
        value = self.get_from_soup(soup, attribute)
        if value is not None and value != '':
            value = int(value)
        return value

    def set_number_from_soup(self, soup, attribute):
        value = self.get_number_from_soup(soup, attribute)
        setattr(self, attribute, value)


class Game(Scraper):

    @classmethod
    def from_xml(cls, data):
        data = data.read()
        soup = BeautifulSoup(data, "xml", from_encoding="utf8").boardgame
        for i in soup:
            if isinstance(i, unicode) and i.strip() == '':
                i.extract()

        game = Game()
        game.objectid = soup['objectid']

        game.name = []
        first_name = None
        for name_tag in soup.find_all("name", recursive=False):
            name = name_tag.string
            if name_tag.get('primary') == 'true':
                first_name = name.strip()
            else:
                game.name.append(name.strip())
                game.name.sort()
            name_tag.extract()
        if first_name is not None:
            game.name.insert(0, first_name)

        for attribute in (
            "yearpublished", "minplayers", "maxplayers", "playingtime",
            "age"):
            game.set_number_from_soup(soup, attribute)

        for attribute in ("description", "thumbnail"):
            game.set_from_soup(soup, attribute)

        i = soup.image
        if i:
            game.image = i.text
        else:
            game.image = None

        game.collect_comments(soup)

        for list_name in (
            'boardgamedesigner', 'boardgamepublisher',
            'boardgamecategory', 'boardgamesubdomain',
            'boardgamehonor', 'boardgamepodcastepisode',
            'boardgameversion', 'boardgamefamily', 'boardgamemechanic',
            'boardgameartist'):
            game.collect_list_from_soup(soup, list_name)

        game.collect_numplayers_poll(soup)
        game.collect_language_dependence_poll(soup)
        game.collect_player_age_poll(soup)

        # any other polls?
        game.collect_polls_from_soup(soup)

        game.collect_ranks(soup)
        game.collect_stats(soup)
        return game


    def collect_numplayers_poll(self, soup):
        poll_tag = soup.find("poll", {"name": "suggested_numplayers"},
                             recursive=False)
        self.numplayers = {}
        if poll_tag is None:
            return
        for results in poll_tag.find_all('results'):
            key = results['numplayers']
            self.numplayers[key] = []
            for value in 'Best', 'Recommended', 'Not Recommended':
                result = results.find("result", value=value)
                if result is not None:
                    result = result['numvotes']
                self.numplayers[key].append(result)
        poll_tag.extract()

    def collect_language_dependence_poll(self, soup):
        poll_tag = soup.find("poll", {"name": "language_dependence"},
                             recursive=False)
        self.language_dependence = {}
        if poll_tag is None:
            return
        for result in poll_tag.find_all('result'):
            key = int(result['level'])
            self.language_dependence[key] = int(result['numvotes'])
        poll_tag.extract()

    def collect_player_age_poll(self, soup):
        poll_tag = soup.find("poll", {"name": "suggested_playerage"},
                             recursive=False)
        self.suggested_player_age = {}
        if poll_tag is None:
            return
        for result in poll_tag.find_all('result'):
            key = result['value']
            self.suggested_player_age[key] = int(result['numvotes'])
        poll_tag.extract()

    def collect_polls_from_soup(self, soup):
        for poll_tag in soup.find_all("poll", recursive=False):
            print "WEIRD POLL DUDE %s" % unicode(poll_tag)

    def collect_comments(self, soup):
        self.comments = []
        for comment_tag in soup.find_all("comment", recursive=False):
            rating = comment_tag.get('rating')
            if rating == 'N/A':
                rating = None
            else:
                rating = float(rating)
            comment = [
                comment_tag.get('username'), rating,
                "\n".join(unicode(x).strip() for x in comment_tag.contents)]
            self.comments.append(comment)
            comment_tag.extract()

    def float(self, v):
        if not v:
            return None
        return float(v)

    def collect_stats(self, soup):
        self.rating = {}
        self.rating['num_responses'] = self.get_tag_value(soup, 'usersrated')
        self.rating['average'] = self.float(self.get_tag_value(soup, 'average'))
        self.rating['bayes_average'] = self.float(
            self.get_tag_value(soup,'bayesaverage'))
        self.rating['stddev'] = self.float(self.get_tag_value(soup, 'stddev'))
        self.rating['median'] = self.float(self.get_tag_value(soup, 'median'))

        self.weight = {}
        self.weight['num_responses'] = self.get_tag_value(soup, 'numweights')
        self.weight['average'] = self.get_tag_value(soup, 'averageweight')

        self.ownership = {}
        self.ownership['commented'] = self.get_tag_value(soup, 'numcomments')
        self.ownership['owned'] = self.get_tag_value(soup, 'owned')
        self.ownership['trading'] = self.get_tag_value(soup, 'trading')
        self.ownership['wanting'] = self.get_tag_value(soup, 'wanting')
        self.ownership['wishing'] = self.get_tag_value(soup, 'wishing')

    def collect_list_from_soup(self, soup, attribute):
        l = []
        for tag in soup.find_all(attribute, recursive=False):
            objectid = tag['objectid']
            contents = tag.string.strip()
            tag.extract()
            l.append([contents, objectid])
        new_attr = attribute
        if attribute.startswith('boardgame'):
            new_attr = attribute[9:]
        setattr(self, new_attr, l)

    def collect_ranks(self, soup):
        self.ranks = {}
        for rank in soup.find_all('rank'):
            name = rank['name']
            friendly_name = rank['friendlyname']
            value = rank['value']
            type = rank['type']
            bayes_average = rank['bayesaverage']
            self.ranks[name] = [friendly_name, value, type, bayes_average]
            rank.extract()



class Geeklist(Scraper):

    @classmethod
    def from_xml(self, data):
        geek = Geeklist()
        soup = BeautifulSoup(data, "xml", from_encoding="utf8")
        if soup.error is not None:
            return None
        soup = soup.geeklist
        if not soup:
            return None
        geek.gather_edits(soup)

        for key in 'username', 'title', 'description':
            geek.set_from_soup(soup, key)

        geek.postdate = geek.get_date_from_soup(soup, 'postdate')
        geek.set_number_from_soup(soup, 'thumbs')

        geek.gather_items(soup)
        geek.gather_comments(soup)
        return geek

    def gather_edits(self, soup):
        self.edits = []
        for timestamp in soup.find_all('editdate'):
            self.edits.append(parse(timestamp.string))

    def gather_items(self, soup):
        self.items = []
        for item_tag in soup.find_all('item', recursive=False):
            item = {}
            for key in (
                'objecttype', 'subtype', 'objectid', 'objectname',
                'username', 'thumbs', 'imageid'):
                item[key] = item_tag[key]
            item['postdate'] = parse(item_tag['postdate'])
            item['editdate'] = parse(item_tag['editdate'])
            item['body'] = self.contents_string(item_tag.body)
            item['comments'] = []
            for comment_tag in item_tag.find_all('comment', recursive=False):
                item['comments'].append(self.comment_from(comment_tag))
            self.items.append(item)

    def gather_comments(self, soup):
        self.comments = [
            self.comment_from(comment_tag) for comment_tag in
                soup.find_all('comment', recursive=False)]

    def comment_from(self, tag):
        comment = {}
        comment['username'] = tag['username']
        comment['thumbs'] = int(tag['thumbs'])
        comment['postdate'] = parse(tag['postdate'])
        comment['postdate'] = parse(tag['editdate'])
        comment['body'] = self.contents_string(tag)
        return comment
