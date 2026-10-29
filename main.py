import sqlite3


def init_db():
  conn = sqlite3.connect('magazin_pro.db')
  cursor = conn.cursor()

  # Таблица товаров
  cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            barcode TEXT UNIQUE,
            price REAL NOT NULL,
            cost_price REAL NOT NULL,
            quantity REAL NOT NULL
        )
    ''')

  # Таблица клиентов для долгов (Ak hasap)
  cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            phone TEXT,
            balance REAL DEFAULT 0.0
        )
    ''')

  # Таблица истории продаж
  cursor.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            customer_name TEXT,
            product_name TEXT,
            quantity REAL,
            total_amount REAL,
            profit REAL,
            payment_type TEXT
        )
    ''')

  # Таблица погашения долгов
  cursor.execute('''
        CREATE TABLE IF NOT EXISTS debt_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            customer_name TEXT,
            amount REAL
        )
    ''')

  # Таблица изъятия денег из кассы (для дома / инкассация)
  cursor.execute('''
        CREATE TABLE IF NOT EXISTS cash_withdrawals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            amount REAL NOT NULL,
            comment TEXT
        )
    ''')

  conn.commit()
  conn.close()


def add_product(name, barcode, price, cost_price, quantity):
  conn = sqlite3.connect('magazin_pro.db')
  cursor = conn.cursor()
  try:
    cursor.execute(
        'INSERT INTO products (name, barcode, price, cost_price, quantity)'
        ' VALUES (?, ?, ?, ?, ?)',
        (name, barcode, price, cost_price, quantity),
    )
    conn.commit()
    print(f"\n✅ Товар '{name}' успешно добавлен на склад!")
  except sqlite3.IntegrityError:
    print(f"\n❌ Ошибка: Товар со штрихкодом '{barcode}' уже существует.")
  finally:
    conn.close()


def add_customer(name, phone):
  conn = sqlite3.connect('magazin_pro.db')
  cursor = conn.cursor()
  try:
    cursor.execute(
        'INSERT INTO customers (name, phone, balance) VALUES (?, ?, 0.0)',
        (name, phone),
    )
    conn.commit()
    print(f"\n✅ Клиент '{name}' успешно добавлен в Ak hasap!")
  except sqlite3.IntegrityError:
    print(f"\n❌ Ошибка: Клиент с именем '{name}' уже есть в базе.")
  finally:
    conn.close()


def show_inventory():
  conn = sqlite3.connect('magazin_pro.db')
  cursor = conn.cursor()
  cursor.execute('SELECT name, barcode, price, cost_price, quantity FROM products')
  products = cursor.fetchall()
  print('\n--- 📦 СКЛАД И ОСТАТКИ ТОВАРОВ ---')
  if not products:
    print('Склад пуст.')
    conn.close()
    return

  low_stock = []
  for p in products:
    name, barcode, price, cost, qty = p
    status = '⚠️ МАЛО!' if qty <= 5 else '✅'
    print(
        f'📦 {name} (Штрихкод: {barcode}) | Цена: {price} ман. | Остаток:'
        f' {qty} шт. {status}'
    )
    if qty <= 5:
      low_stock.append(name)

  if low_stock:
    print(
        f'\n⚠️ ВНИМАНИЕ: Заканчиваются товары: {", ".join(low_stock)}. Срочно'
        ' докупите у поставщика!'
    )
  conn.close()


def search_product(query):
  conn = sqlite3.connect('magazin_pro.db')
  cursor = conn.cursor()
  cursor.execute(
      'SELECT name, barcode, price, quantity FROM products WHERE name LIKE ? OR'
      ' barcode = ?',
      (f'%{query}%', query),
  )
  results = cursor.fetchall()
  print(f'\n--- 🔍 РЕЗУЛЬТАТЫ ПОИСКА: "{query}" ---')
  if not results:
    print('Ничего не найдено.')
  else:
    for r in results:
      print(
          f'Товар: {r[0]} | Штрихкод: {r[1]} | Цена: {r[2]} ман. | Остаток:'
          f' {r[3]} шт.'
      )
  conn.close()


def show_customers_debt():
  conn = sqlite3.connect('magazin_pro.db')
  cursor = conn.cursor()
  cursor.execute('SELECT name, phone, balance FROM customers')
  customers = cursor.fetchall()
  print('\n--- 👤 AK HASAP (ДОЛГИ ПОКУПАТЕЛЕЙ) ---')
  if not customers:
    print('Список должников пуст.')
    conn.close()
    return

  total_debt = 0
  for c in customers:
    name, phone, balance = c
    print(f'Клиент: {name} | Тел: {phone} | Долг: {balance} манат')
    total_debt += balance
  print(f'\n📌 Общая сумма всех долгов в магазине: {total_debt} манат')
  conn.close()


# НОВАЯ ФУНКЦИЯ: История покупок клиента
def show_customer_history(customer_name):
  conn = sqlite3.connect('magazin_pro.db')
  cursor = conn.cursor()
  cursor.execute(
      'SELECT date, product_name, quantity, total_amount, payment_type FROM'
      ' sales WHERE customer_name = ?',
      (customer_name,),
  )
  sales = cursor.fetchall()
  print(f'\n--- 📜 ИСТОРИЯ ПОКУПОК КЛИЕНТА: {customer_name} ---')
  if not sales:
    print('У этого клиента пока нет записей о покупках.')
  else:
    for s in sales:
      print(
          f'📅 [{s[0]}] Товар: {s[1]} | Ков: {s[2]} шт. | Сумма: {s[3]} ман.'
          f' | Тип: {s[4]}'
      )
  conn.close()


def make_sale(customer_name, barcode, count, payment_type):
  conn = sqlite3.connect('magazin_pro.db')
  cursor = conn.cursor()

  cursor.execute(
      'SELECT id, name, price, cost_price, quantity FROM products WHERE'
      ' barcode = ?',
      (barcode,),
  )
  product = cursor.fetchone()

  if not product:
    print('\n❌ Ошибка: Товар со штрихкодом не найден!')
    conn.close()
    return

  prod_id, prod_name, price, cost_price, stock_qty = product

  if stock_qty < count:
    print(
        f'\n❌ Ошибка: Недостаточно товара "{prod_name}" на складе! Остаток:'
        f' {stock_qty}'
    )
    conn.close()
    return

  total_price = price * count
  total_cost = cost_price * count
  profit = total_price - total_cost

  new_stock = stock_qty - count
  cursor.execute(
      'UPDATE products SET quantity = ? WHERE id = ?', (new_stock, prod_id)
  )

  actual_customer = 'Обычный покупатель'
  if payment_type == 'debt':
    if not customer_name:
      print('\n❌ Ошибка: Для продажи в долг обязательно укажите имя клиента!')
      conn.rollback()
      conn.close()
      return

    actual_customer = customer_name
    cursor.execute('SELECT id FROM customers WHERE name = ?', (customer_name,))
    cust = cursor.fetchone()
    if not cust:
      cursor.execute(
          'INSERT INTO customers (name, balance) VALUES (?, ?)',
          (customer_name, total_price),
      )
    else:
      cursor.execute(
          'UPDATE customers SET balance = balance + ? WHERE name = ?',
          (total_price, customer_name),
      )
    print(
        f'\n🛒 Продано в долг: {prod_name} ({count} шт.) на сумму'
        f' {total_price} манат. Клиент: {customer_name}'
    )
  else:
    pay_name_ru = (
        'Наличные' if payment_type == 'cash' else 'Банковская карта'
    )
    if customer_name:
      actual_customer = customer_name
    print(
        f'\n💵 Продажа ({pay_name_ru}): {prod_name} ({count} шт.) на сумму'
        f' {total_price} манат.'
    )

  cursor.execute(
      'INSERT INTO sales (customer_name, product_name, quantity, total_amount,'
      ' profit, payment_type) VALUES (?, ?, ?, ?, ?, ?)',
      (
          actual_customer,
          prod_name,
          count,
          total_price,
          profit,
          payment_type,
      ),
  )

  conn.commit()
  conn.close()


def pay_debt(customer_name, amount):
  conn = sqlite3.connect('magazin_pro.db')
  cursor = conn.cursor()
  cursor.execute('SELECT balance FROM customers WHERE name = ?', (customer_name,))
  cust = cursor.fetchone()
  if not cust:
    print(f"\n❌ Ошибка: Клиент '{customer_name}' не найден в базе должников!")
    conn.close()
    return

  cursor.execute(
      'UPDATE customers SET balance = balance - ? WHERE name = ?',
      (amount, customer_name),
  )
  cursor.execute(
      'INSERT INTO debt_payments (customer_name, amount) VALUES (?, ?)',
      (customer_name, amount),
  )
  conn.commit()
  conn.close()
  print(
      f"\n💰 Погашение долга: клиент '{customer_name}' внес в кассу {amount}"
      ' манат.'
  )


def withdraw_cash_from_register(amount, comment):
  conn = sqlite3.connect('magazin_pro.db')
  cursor = conn.cursor()
  cursor.execute(
      'INSERT INTO cash_withdrawals (amount, comment) VALUES (?, ?)',
      (amount, comment),
  )
  conn.commit()
  conn.close()
  print(
      f'\n📤 Из кассы извлечено: {amount} манат. Назначение: "{comment}".'
  )


def show_financial_report():
  conn = sqlite3.connect('magazin_pro.db')
  cursor = conn.cursor()

  cursor.execute(
      'SELECT SUM(total_amount), SUM(profit) FROM sales WHERE payment_type ='
      " 'cash'"
  )
  cash_sales_res = cursor.fetchone()
  cash_sales = (
      cash_sales_res[0] if cash_sales_res and cash_sales_res[0] else 0.0
  )
  cash_profit = (
      cash_sales_res[1] if cash_sales_res and cash_sales_res[1] else 0.0
  )

  cursor.execute(
      'SELECT SUM(total_amount), SUM(profit) FROM sales WHERE payment_type ='
      " 'card'"
  )
  card_sales_res = cursor.fetchone()
  card_sales = (
      card_sales_res[0] if card_sales_res and card_sales_res[0] else 0.0
  )
  card_profit = (
      card_sales_res[1] if card_sales_res and card_sales_res[1] else 0.0
  )

  total_revenue = cash_sales + card_sales
  total_profit = cash_profit + card_profit

  cursor.execute('SELECT SUM(amount) FROM debt_payments')
  debt_pay_res = cursor.fetchone()
  total_debt_payments = (
      debt_pay_res[0] if debt_pay_res and debt_pay_res[0] else 0.0
  )

  cursor.execute('SELECT SUM(amount) FROM cash_withdrawals')
  withdrawal_res = cursor.fetchone()
  total_withdrawals = (
      withdrawal_res[0] if withdrawal_res and withdrawal_res[0] else 0.0
  )

  physical_cash_in_drawer = (
      cash_sales + total_debt_payments - total_withdrawals
  )

  cursor.execute(
      'SELECT SUM(total_amount) FROM sales WHERE payment_type = "debt"'
  )
  res_debt_sales = cursor.fetchone()
  total_debt_sales = (
      res_debt_sales[0] if res_debt_sales and res_debt_sales[0] else 0.0
  )

  cursor.execute('SELECT SUM(balance) FROM customers')
  res_debts = cursor.fetchone()
  current_debts = res_debts[0] if res_debts and res_debts[0] else 0.0

  print('\n====================================')
  print('   📊 ФИНАНСОВЫЙ ОТЧЕТ И КАССА')
  print('====================================')
  print(f'💵 Продажи за наличные: {cash_sales} манат')
  print(f'💳 Продажи по карте: {card_sales} манат')
  print(f'💰 Возвраты долгов в кассу: {total_debt_payments} манат')
  print(f'📤 Всего забрано из кассы (для дома): {total_withdrawals} манат')
  print(f'🗄️ ОСТАТОК НАЛИЧНЫХ В КАССЕ: {physical_cash_in_drawer} манат')
  print('------------------------------------')
  print(f'📈 Общая чистая прибыль магазина: {total_profit} манат')
  print(f'📝 Отпущено товаров в долг всего: {total_debt_sales} манат')
  print(f'👥 Актуальный долг клиентов (Ak hasap): {current_debts} манат')
  print('====================================')
  conn.close()


# НОВАЯ ФУНКЦИЯ: Экспорт отчета в файл
def export_report_to_file():
  conn = sqlite3.connect('magazin_pro.db')
  cursor = conn.cursor()

  cursor.execute(
      'SELECT SUM(total_amount) FROM sales WHERE payment_type = "cash"'
  )
  cs = cursor.fetchone()
  cash_s = cs[0] if cs and cs[0] else 0.0

  cursor.execute(
      'SELECT SUM(total_amount) FROM sales WHERE payment_type = "card"'
  )
  cds = cursor.fetchone()
  card_s = cds[0] if cds and cds[0] else 0.0

  cursor.execute('SELECT SUM(balance) FROM customers')
  cd = cursor.fetchone()
  cur_debt = cd[0] if cd and cd[0] else 0.0

  filename = 'magazin_otchet.txt'
  with open(filename, 'w', encoding='utf-8') as f:
    f.write('=== ОФИЦИАЛЬНЫЙ ОТЧЕТ МАГАЗИНА (AK HASAP) ===\n')
    f.write(f'Продажи за наличные: {cash_s} манат\n')
    f.write(f'Продажи по карте: {card_s} манат\n')
    f.write(f'Общий долг клиентов (Ak hasap): {cur_debt} манат\n')

  print(f'\n📁 Отчет успешно сохранен в текстовый файл: "{filename}"')
  conn.close()


def main():
  init_db()

  while True:
    print('\n====================================')
    print('   PRO МАГАЗИН & AK HASAP v3.0')
    print('====================================')
    print('1. 📦 Посмотреть склад (и остатки)')
    print('2. 🔍 Найти товар по названию/штрихкоду')
    print('3. 👥 Посмотреть Ak hasap (долги)')
    print('4. 📜 История покупок клиента')
    print('5. ➕ Добавить новый товар')
    print('6. 👤 Добавить нового клиента')
    print('7. 🛒 Продать товар (Наличные / Карта / Долг)')
    print('8. 💰 Погасить долг клиента')
    print('9. 📤 Забрать деньги из кассы (для дома)')
    print('10. 📊 Финансовый отчет и касса')
    print('11. 📁 Экспорт отчета в файл')
    print('0. 🚪 Выход')

    choice = input('\nВыберите номер пункта (0-11): ').strip()

    if choice == '1':
      show_inventory()
    elif choice == '2':
      q = input('Введите название или штрихкод товара для поиска: ')
      search_product(q)
    elif choice == '3':
      show_customers_debt()
    elif choice == '4':
      c_name = input('Введите имя клиента для просмотра истории: ')
      show_customer_history(c_name)
    elif choice == '5':
      name = input('Введите название товара: ')
      barcode = input('Введите штрихкод: ')
      try:
        price = float(input('Цена продажи (манат): '))
        cost_price = float(input('Себестоимость (манат): '))
        quantity = float(input('Количество на складе: '))
        add_product(name, barcode, price, cost_price, quantity)
      except ValueError:
        print('\n❌ Ошибка: вводите числа для цен и количества!')
    elif choice == '6':
      name = input('Имя клиента: ')
      phone = input('Номер телефона: ')
      add_customer(name, phone)
    elif choice == '7':
      print('\n--- ВЫБЕРИТЕ ТИП ОПЛАТЫ ---')
      print('1. Наличные')
      print('2. Банковская карта')
      print('3. В долг (Ak hasap)')
      p_type = input('Ваш выбор (1-3): ').strip()

      payment_type = 'cash'
      customer_name = ''

      if p_type == '2':
        payment_type = 'card'
      elif p_type == '3':
        payment_type = 'debt'
        customer_name = input('Введите имя клиента: ')

      barcode = input('Введите штрихкод товара: ')
      try:
        count = float(input('Количество для продажи: '))
        make_sale(customer_name, barcode, count, payment_type)
      except ValueError:
        print('\n❌ Ошибка: введите число для количества!')
    elif choice == '8':
      customer_name = input('Имя клиента: ')
      try:
        amount = float(input('Сумма оплаты (сколько манат внес в кассу): '))
        pay_debt(customer_name, amount)
      except ValueError:
        print('\n❌ Ошибка: введите число для суммы!')
    elif choice == '9':
      try:
        amount = float(input('Сколько манат забираете из кассы: '))
        comment = input(
            'На что/куда забираете (например: "Для дома", "На закупку"): '
        )
        withdraw_cash_from_register(amount, comment)
      except ValueError:
        print('\n❌ Ошибка: введите число для суммы!')
    elif choice == '10':
      show_financial_report()
    elif choice == '11':
      export_report_to_file()
    elif choice == '0':
      print('\nПрограмма завершена. До свидания!')
      break
    else:
      print('\n❌ Неверный выбор! Пожалуйста, выберите цифру от 0 до 11.')


if __name__ == '__main__':
  main()
