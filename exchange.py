# -*- coding: utf-8 -*-
# Author: Konstantin Polyakov
# Date: 25.07.2014, 18.08.2015, 06.11.2015, 18.06.2016

import json, hmac, hashlib, os, time
from urllib import request, parse

import requests
import serial # pip3 install pyserial

# Класс для удобного вызова АПИ.

class Doer:
    def __init__(self, classObj):  self.c = classObj
    def __getattr__(self, api_name, *args): return lambda **args: self.c.shell(api_name, args)

# Класс  протоАПИ бирж

class proAPI:
    def __init__(self, conf):
      self.conf = conf
      self.do = Doer(self)

    
    #self.opener = request.build_opener(request.HTTPCookieProcessor(cj))

    def urlopen(self, url, POST={}, GET={}, headers={}):
        if POST: r = requests.post(url, params=GET, data=POST, headers=headers)
        else: r = requests.get(url, params=GET, headers=headers)

        if r.status_code == 200:
            return r.text, True, []
        else:
            error = r.status_code +' '+ r.message
            return r.text, False, [error]

# Класс цены

class Price():
    def __init__(self, pair, buy, sell):
        self.pair = pair
        self.buy = float(buy)
        self.sell = float(sell)
        self.calc_base_values()
        #self.glass_buy = None
        #self.glass_sell = None
    def calc_base_values(self): # расчёт основных величин
        self.spread = self.buy - self.sell # спрэд
        self.mean = (self.buy + self.sell) / 2 # среднее арифметическое

# Классы АПИ бирж

class exchange_exmo(proAPI):
    exmo_url = "https://api.exmo.com/v1/"

    def sign(self, data):
        return hmac.new(key=bytearray(self.conf['secret'], 'utf-8'), msg=data, digestmod=hashlib.sha512).hexdigest()

    def shell(self, api_name, api_params):
        if api_name.startswith('_'): # Auth API
            api_name = api_name[1:]
            api_params["nonce"] = str(time.time()).replace('.', '')#split('.')[0]
            sign = self.sign(bytearray(parse.urlencode(api_params), 'utf-8'))
            header = {"Key": self.conf['key'], "Sign":sign}
            data, success, errors = self.urlopen(self.exmo_url + api_name, POST=api_params, headers=header)
        else: # Public API
            data, success, errors = self.urlopen(self.exmo_url + api_name, GET=api_params)

        if success:
            data = json.loads(data)
            return (data, True, errors) if 'error' not in data else (None, False, errors+[data])
        else: return None, False, errors

    def price(self, upair):
        pair = upair.replace('-', '_').upper()

        data, success, errors = self.do.order_book(pair=pair, limit=0)
        if success:
            if pair in data: data = data[pair]
            else: errors.append('Нет информации по валютной паре '+pair)
        else: success = False

        if not success: return data, success, errors

        price = Price(upair, data['ask_top'], data['bid_top'])
        #price.glass_sell = data['bid']
        #price.glass_buy = data['ask']

        return price, success, errors

    def new_order(self, pair, action, quantity, price):
        pair = pair.replace('-', '_').upper()
        if price == 'market':
            price = 0
            action = market +'_'+ action
        data, success, errors = self.do._order_create(pair=pair, quantity=quantity, price=price, type=action)
        return data, success, errors

    def cancel_order(self, order_id):
        data, success, errors = self.do._order_cancel(order_id=order_id)
        return data, success, errors

class exchange_btce(proAPI):
    btce_url = "https://btc-e.nz/tapi"
    btce_url2 = "https://btc-e.nz/api/3/%s/%s"
    __wait_for_nonce = False # for btce

    def shell(self, api_name, api_params):
        if self.__wait_for_nonce: time.sleep(1)
        if api_name.startswith('_'): # Auth API
            api_name = api_name[1:]
            nonce_v = str(time.time()).split('.')[0]
            api_params['method'] = api_name
            api_params['nonce'] = nonce_v
            post_data = bytearray(parse.urlencode(api_params), 'utf-8')
            sign = hmac.new(bytearray(self.conf['secret'], 'utf-8'), post_data, digestmod=hashlib.sha512).hexdigest()
            headers = {"Content-type" : "application/x-www-form-urlencoded",
                       "Key" : self.conf['key'],
                       "Sign" : sign}
            data, success, errors = self.urlopen(self.btce_url, POST=post_data, headers=headers)
        else: # Public API
            api_params = '' if 'pairs' not in api_params else '-'.join(api_params['pairs'])
            data, success, errors = self.urlopen(self.btce_url2 % (api_name, api_params), headers={'Host':'btc-e.nz', 'Accept': 'application/json', 'Accept-Charset': 'utf-8', 'Accept-Encding': 'identity', 'Connection': 'keep-alive'})

        if success:
            data = json.loads(data)
            return (data, True, errors) if 'error' not in data else (None, False, errors+[data])
        else: return None, False, errors

    def price(self, upair=None): # upair is universal pair
        pair = upair.replace('-', '_')
        pair = pair.replace('rub', 'rur')

        data, success, errors = self.do.ticker(pairs=[pair])
        if success:
            if pair in data: data = data[pair]
            else: errors.append('Нет информации по валютной паре '+pair)
        else: success = False

        if not success: return data, success, errors

        price = Price(upair, data['buy'], data['sell'])

        return price, success, errors

    def new_order(self, pair, action):
        pass

    def cancel_order(self, order_id):
        data, success, errors = self.do._CancelOrder(order_id=order_id)
        return data, success, errors

# ---------------------- Старый вариант -----------
class API():
  exmo_url = "https://api.exmo.com/v1/"
  btce_url = "https://btc-e.com/tapi"
  btce_url2 = "https://btc-e.com/api/3/%s/%s"
  __wait_for_nonce = False

  def __init__(self, conf):
    self.conf = conf
    self.exmo_it = request.build_opener()#internettools.InternetTools(geterrors=True)
    self.btce_it = request.build_opener()#internettools.InternetTools(geterrors=True)
    self.opener = request.build_opener()

  def __getattr__(self, api_name, *args):
    return lambda **args: self.shell(api_name, args)

  def urlopen(self, url, POST=None, GET=None, headers={}):
    if isinstance(POST, dict): POST = parse.urlencode(POST)
    if isinstance(GET, dict): GET = parse.urlencode(GET)
    if GET != None: url += '?' + GET

    self.opener.addheaders.extend(headers.items())
    try: response = self.opener.open(url, POST)
    except Exception as e: return e.reason, None, None
    str_page = response.read()

    return None, str_page, response

  def exmo_shell(self, api_name, api_params):
    if api_name.startswith('_'): # Auth API
      api_name = api_name[1:]
      api_params["nonce"] = str(time.time()).replace('.', '')#split('.')[0]
      post_data = bytearray(parse.urlencode(api_params), 'utf-8')
      sign = hmac.new(key=bytearray(self.conf['exmo']['secret'], 'utf-8'), msg=post_data, digestmod=hashlib.sha512).hexdigest()
      header = {"Key": self.conf['exmo']['key'], "Sign":sign}
      #print header
      answer = self.urlopen(self.exmo_url + api_name, POST=post_data, headers=header)
    else: # Public API
      answer = self.urlopen(self.exmo_url + api_name, GET=api_params, headers={'Accept-Charset': 'utf-8' })
    if answer[0] == None: return True, json.loads(str(answer[1], 'utf-8'))
    else: return False, answer[0]

  def btce_shell(self, api_name, api_params):
    if self.__wait_for_nonce: time.sleep(1)
    if api_name[0] == '_': # Auth API
      api_name = api_name[1:]
      nonce_v = str(time.time()).split('.')[0]
      api_params['method'] = api_name
      api_params['nonce'] = nonce_v
      post_data = bytearray(parse.urlencode(api_params), 'utf-8')
      sign = hmac.new(bytearray(self.conf['btce']['secret'], 'utf-8'), post_data, digestmod=hashlib.sha512).hexdigest()
      headers = {"Content-type" : "application/x-www-form-urlencoded",
                     "Key" : self.conf['btce']['key'],
                     "Sign" : sign}
      answer = self.urlopen(self.btce_url, POST=post_data, headers=headers)
    else: # Public API
      answer = self.urlopen(self.btce_url2 % (api_name, api_params['pairs']))
    if answer[0] == None: return True, json.loads(str(answer[1], 'utf-8'))
    else: return False, answer[0]

  def shell(self, api_name, api_params):
    print("---------")
    #if api_name == 'exmo': return 
    #return self.__getattribute__(name+'_shell')(api_name, api_params)
    name, api_name = api_name.split('_', 1)
    return self.__getattribute__(name+'_shell')(api_name, api_params)

  '''# ########## Высоуровневые функции ############
  def normalize_pair(self, ec_name, pair):
    if ec_name=='exmo': return pair.upper()
    elif ec_name=='btce': return pair.replace('rub', 'rur')

  def denormalize_pair(self, ec_name, pair):
    if ec_name=='exmo': return pair.lower()
    elif ec_name=='btce': return pair.replace('rur', 'rub')

  def Price(self, ec_name, pair, _type):
    ''' '''Пары пишутся маленькими буквами. Рубль - это rub. ''' '''
    pair = self.normalize_pair(ec_name, pair)
    if ec_name == 'exmo':
      if _type=='buy': _type = 'sell'
      elif _type=='sell': _type = 'buy'
      answer = self.exmo_ticker()
      return float(answer[pair][_type+'_price'])
    elif ec_name == 'btce':
      answer = self.btce_ticker(pairs=pair)
      return float(answer[pair][_type])

  def PairsList(self, ec_name):
    if ec_name == 'exmo': pairs = self.exmo_ticker().keys()
    elif ec_name == 'btce': pairs = self.btce_info(pairs='')['pairs'].keys()
    else: print(ec_name, '| Wrong name of exchange!')
    return [self.denormalize_pair(ec_name, pair) for pair in pairs]

  def PairsTradeInfo(self, ec_name):
    if ec_name == 'exmo':
      _pairs = self.exmo_ticker() # список пар с ценами
      return {self.denormalize_pair(ec_name, pair): {'buy': float(data['sell_price']), 'sell': float(data['buy_price'])} for pair, data in _pairs.items()} # sell -> buy - это не ошибка!
    elif ec_name == 'btce':
      _pairs = self.btce_info(pairs='')['pairs'].keys() # список пар с настройками
      _pairs = self.btce_ticker(pairs='-'.join(_pairs)) # передав список, получаем и список, и цены
      for key, value in _pairs.items():
        try: _pairs[key] = float(value)
        except: pass
      return {self.denormalize_pair(ec_name, pair): data for pair, data in _pairs.items()}'''
# -------------------------------------------------

if __name__ == '__main__':

    # Тест бирж

    import configparser, os
    config = configparser.ConfigParser()
    path_conf = os.path.join(os.path.dirname(os.path.abspath('')), 'conf_exchange.txt')
    config.read(path_conf)

    exmo = exchange_exmo(config['exmo'])
    btce = exchange_btce(config['btce'])
    #print()
    print(exmo.do._user_info())
    #print()
    #print(btce.do.info(pairs=[]))
    #print(btce.do._getInfo())
    print('\n\n')

    price, success, errs = exmo.price('btc-usd')
    print(price.buy, price.sell, price.spread)

    price, success, errs = btce.price('btc-usd')
    print(price.buy, price.sell, price.spread)

    def fprice(price_float):
        return '{0:<15}'.format(price_float)

    threshold = { # пороговые значения
        'eth-rub': {'max_buy':759, 'max_sell':750}
    }

    while True:

        price, success, errs = exmo.price('eth-rub')
        if success:
            print('EXMO:', fprice(price.buy), price.sell)
            if (price.sell > threshold['eth-rub']['max_sell']): print('MAX SELL PRICE IS OBTAINED')
        else: print('EXMO: ERROR:', errs)

        price, success, errs = btce.price('eth-rub')
        if success:
            print('BTCE:', fprice(price.buy), price.sell)
        else: print('BTCE: ERROR:', errs)

        print()

        time.sleep(10)