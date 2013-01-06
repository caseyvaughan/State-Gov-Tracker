## Functions to login to cicero
## Identify state representatives by address using cicero

from login_credentials import BING_KEY, cicero_user, cicero_password
import urllib, httplib2, mimetypes, os, sys, re, random, string
from geopy import geocoders

####SETTINGS####
http = httplib2.Http()


import json


def _filter_addresses(list_of_tuples):
    """ Helper function to filter out addresses not in PA """
    filtered_list = []
    for geocoded_address in list_of_tuples:
        if geocoded_address[0].find(', PA ') != -1:
            filtered_list.append(geocoded_address)
    return filtered_list


class LegislatorFinder():
    """Class to upper and lower state level districts for pennsylvania"""
    def __init__(self):
        self.user = cicero_user
        self.password = cicero_password
        self.cicero_url = 'http://cicero.azavea.com'
        self.headers = {'Content-type': 'application/x-www-form-urlencoded'}

    def login(self):
        url = '/v3.1/token/new.json'
        body = {'username': self.user, 'password': self.password}
        response, content = http.request(self.cicero_url + url, 'POST', headers=self.headers, body=urllib.urlencode(body))
        content_dict = json.loads(content)
        self.token = content_dict['token']
        self.uid = content_dict['user']

    def _filter_districts(self):
        for district in self.district_data['response']['results']['districts']:
            if district['district_type'] == 'STATE_UPPER':
                self.upper = district['district_id']
            if district['district_type'] == 'STATE_LOWER':
                self.lower = district['district_id']

    def geocode_address(self, origin_address):
        self.places = []
        b = geocoders.Bing(BING_KEY)
        try:
            place, (lat, lng) = b.geocode(origin_address)
            self.places.append((place, lat, lng))
        except ValueError:
            for result in b.geocode(origin_address, exactly_one=False):
                place, (lat, lng) = result
                self.places.append((place, lat, lng))
        except:
            self.places.append(None)
        self.places = _filter_addresses(self.places)
        if len(self.places) > 1:
            raise ValueError("More than one location found")
        if len(self.places) == 0:
            raise LookupError("No Locations in PA found")
        else:
            self.lat = self.places[0][1]
            self.lng = self.places[0][2]

    def find_leg_districts(self, lat=None, lng=None):
        self.login()
        if lat and lng:
            url = '/v3.1/legislative_district?user=%s&token=%s&lat=%s&lon=%s' % (self.uid, self.token, lat, lng)
            print url
            response, content = http.request(self.cicero_url + url, 'GET', headers=self.headers)
            self.district_data = json.loads(content)
        elif len(self.places) == 1:
            url = '/v3.1/legislative_district?user=%s&token=%s&lat=%s&lon=%s' % (self.uid, self.token, self.lat, self.lng)
            print url
            response, content = http.request(self.cicero_url + url, 'GET', headers=self.headers)
            self.district_data = json.loads(content)
        self._filter_districts()


def search(request, upper_or_lower):
    if 'q' in request.GET:
        loc = request.GET['q'].replace(' ', '+')
    else:
        loc = '1+Penn+Square+Philadelphia+PA+19107'
    json_response = login(cicero_user, cicero_password)
    token = json_response['token']
    uid = str(json_response['user'])
    official_response = get_officials(loc, uid, token, upper_or_lower)
    official_dict = json.loads(official_response)
    for x in range(1):
        return official_info(official_dict, x)


def get_officials(loc, uid, token, upper_or_lower):
    url = '/official?user=' + uid + '&token=' + token + '&search_loc=' + loc + '&search_country=US&valid_on_or_before=2012-11-01&district_type=STATE_' + upper_or_lower
    headers = {'Content-type': 'application/x-www-form-urlencoded'}
    response, content = http.request(url_base + url, 'GET', headers=headers)
    return content


def find_districts(lat, long, user, token):
    url = '/v3.1/user=%s&token=%slegislative_district?lat=%s&lon=%s' % (user, token, lat, lon)
    response, content = http.request(url_base + url, 'GET', headers=headers)
    json.loads(content)
    return content


def official_info(official_dict, x):
    results = {}
    results['district_id'] = official_dict['response']['results']['candidates'][0]['officials'][x]['office']['district']['district_id']
    results['chamber'] = official_dict['response']['results']['candidates'][0]['officials'][x]['office']['chamber']['name']
    results['first_name'] = official_dict['response']['results']['candidates'][0]['officials'][x]['first_name']
    results['last_name'] = official_dict['response']['results']['candidates'][0]['officials'][x]['last_name']
    results['address'] = str(official_dict['response']['results']['candidates'][0]['officials'][x]['addresses'][0]['address_1']) + ' ' + str(official_dict['response']['results']['candidates'][0]['officials'][x]['addresses'][0]['address_2']) + ' ' + str(official_dict['response']['results']['candidates'][0]['officials'][x]['addresses'][0]['city']) + ', ' + str(official_dict['response']['results']['candidates'][0]['officials'][x]['addresses'][0]['state']) + ' ' + str(official_dict['response']['results']['candidates'][0]['officials'][x]['addresses'][0]['postal_code'])
    results['phone'] = str(official_dict['response']['results']['candidates'][0]['officials'][x]['addresses'][0]['phone_1'])
    return results
