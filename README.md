# Модуль для работы с биржами.

Язык: Python 3.4 

Поддерживаются биржы Exmo и BTC-e. Цель данного модуля - построение универсального интерфейса для бирж.

# Использование

```
import exchange

exmo = exchange.exchange_exmo({'key': '', secret': ''})
btce = exchange.exchange_btce({'key': '', secret': ''})
polo = exchange.exchange_poloniex({'key': '', secret': ''})
```

Обращаться к API можно двумя способами:
- прямое обращение к API биржы - ```exmo.do.имяМетода() или exmo.do._имяМетода()``` - Символ подчёркивания означает метод, использующий авторизацию, без подчёркивания - без авторизации. Полный список методов можно найти в документации соответствующих бирж.
- универсальные методы - ```exmo.имяФункции()``` - вне зависимости от биржы.

Функции обеих катагорий возвращают три значения: результат, наличие ошибки, список ошибок. Всегда в таком порядке

Примеры прямого обращения к биржам:
```
exmo.do._user_info() # запрос информации 
btce.do._getInfo() # то же самое

btce.do.info(pairs=['usd_rur']) # информация о торгах по валютным парам
exmo.do.order_book(pair='USD_RUB', limit=10) # то же самое
```

Обратите внимание на названия валютных пар: для функций прямого обращения правила наименования пар различаются для разных бирж. Но для универсальных функций используется универсальное правило: латнискими буквами в нижнем регистре, в качестве разделителя валют - знак тире

Обращение к API через универсальные функции. Вместо "exmo" можно подставлять любую биржу.

```
price = exmo.price('btc-usd') # получение цены пары. Для Exmo можно указать второй аргумент - количество значений в "стакане"
order = exmo.order('btc-usd', 'buy', 10, 3000) # Создание ордера
```

# Список универсальных функций

## price - получение цены

```
price, success, errors = exmo.price(upair)
if success: print(price.buy, price.sell, price.spread, price.mean)
```

Аргументы:
- upair - имя валютной пары


в случае успеха возвращает объект Price, имеющего следующие свойства:
- ```price.sell``` - цена продажи
- ```price.buy``` - цена покупки
- ```price.spread``` - спред (спред = цена покупки - цена продажи)
- ```price.mean``` - среднее арифметическое цены продажи и цены покупки

## order - создание ордера

```
order, success, errors = exmo.order(upair, action, count, price)
if success: print(order.order_id)
```

Аргументы:
- upair - имя валютной пары
- action - тип ордера: ```"sell"``` или ```"buy"```
- count - количество по ордеру
- price - цена по ордеру.

 
в случае успеха возвращает объект Order, имеющего следующие свойства:
- ```order.order_id``` - id ордера, если ордер выставлен
- ```order.upair``` - аналогично одноимённому аргументу
- ```order.action``` - аналогично одноимённому аргументу
- ```order.count``` - аналогично одноимённому аргументу
- ```order.price``` - аналогично одноимённому аргументу

## cancel_order - отмена ордера 

```
data, success, errors = exmo.cancel_order(order_id)
if success: print('Ордер отменён')
```

Аргументы:
- order_id - id ордера

 
в любом случае возвращает None.