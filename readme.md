# Crypto Trading & Wallet CLI Platform

ტერმინალზე (CLI) დაფუძნებული კრიპტო სავაჭრო და პორტფოლიოს მართვის სისტემა, შექმნილი სუფთა არქიტექტურის (Clean Architecture) და Domain-Driven Design (DDD) პრინციპების დაცვით.

სისტემა ინტეგრირებულია Binance-ის პირდაპირ WebSocket სტრიმთან და მოიცავს ფონურ სავაჭრო ბოტს, რომელიც ავტომატურად ასრულებს ლიმიტირებულ ორდერებს.

---

## ძირითადი ფუნქციონალი

1. **რეალური დროის WebSocket სტრიმინგი (Binance Live Stream)**
   - ტოპ კრიპტოვალუტების ცოცხალი ფასები და 24-საათიანი დინამიკა (+ UP / - DOWN / = FLAT).
   - ფასების მყისიერი განახლება ყოველგვარი ქსელური დაყოვნების გარეშე (`BinanceWSManager`).

2. **საფულის სრული მენეჯმენტი (Wallet Management)**
   - **LIVE საფულის სტრიმი**: ფიატ ბალანსი, კრიპტო აქტივების ცოცხალი შეფასება, PnL, ბოტის აქტიური ორდერები და ბოლო ტრანზაქციები ერთ ეკრანზე.
   - **დეპოზიტი და თანხის გატანა**: ფიატის შეტანა და გატანა ბალანსის ვალიდაციით.
   - **შიდა P2P გადარიცხვა**: USD-ის ან კრიპტოვალუტის გადარიცხვა მომხმარებლებს შორის Username-ით.
   - **ტრანზაქციების ისტორია & CSV ექსპორტი**: ყველა ოპერაციის ჟურნალი და ფაილში ექსპორტი.
   - **პორტფოლიოს განაწილება & LIVE ანალიტიკა**: აქტივების წილი (%) და ღია Unrealized PnL რეალურ დროში.

3. **კრიპტო ბაზარი და ვაჭრობა (Market & Trading)**
   - ბაზრის ყველა წყვილის LIVE სტრიმი.
   - აქტივის ძებნა და ყიდვა/გაყიდვა ინტერაქტიული LIVE პრევიუს ფანჯრით.
   - **რჩეული მონეტები (Watchlist)**: პირადი რჩეული სიის შედგენა და მათი ფასების ცოცხალი მონიტორინგი.
   - **ფასის შეტყობინებები (Price Alerts)**: პირობითი ალერტები (ABOVE / BELOW), რომლებსაც ფონური ბოტი აკონტროლებს.
   - **დღის ტოპ ზრდა / ვარდნა (Top Movers)**: TOP 5 Gainers და Losers რეალურ დროში.

4. **ავტომატური სავაჭრო ბოტი და ორდერები (Order Bot Engine)**
   - ლიმიტირებული ორდერების ტიპები: `BUY_LIMIT`, `SELL_LIMIT`, `STOP_LOSS`.
   - ორდერის განთავსებისას ბალანსის/აქტივის ავტომატური დარეზერვება.
   - პარალელურ ფონურ თრედში (`daemon thread`) ბაზრის ფასების შემოწმება და ორდერების ავტომატური აღსრულება.
   - ორდერის გაუქმება და დარეზერვებული თანხის/აქტივის მომენტალური დაბრუნება საფულეში.
   - ორდერების ცოცხალი მონიტორინგის ეკრანი (`view_orders_menu`).

5. **მომხმარებლის პროფილი და უსაფრთხოება**
   - რეგისტრაცია, ავტორიზაცია, პაროლის დაშიფვრა (Bcrypt) და JWT სესიები.
   - პროფილის სტატისტიკა (ტრანზაქციების, ვაჭრობების და აქტიური ორდერების რაოდენობა).
   - პაროლისა და მომხმარებლის სახელის (Username) შეცვლა უსაფრთხოების წესების შემოწმებით.
   - როლების სისტემა: `ADMIN` და `REGULAR`.

---

## პროექტის არქიტექტურა (Folder Structure)

პროექტი დაყოფილია მკაცრ ფენებად:

```text
Python-app/
├── core/                               # კონფიგურაცია, ბაზის კავშირი, Result Pattern
│   ├── config.py
│   ├── database.py
│   └── result.py
│
├── domain/                             # ბიზნეს ლოგიკა და ენთითები
│   └── aggregates/
│       ├── user/                       # User Aggregate, როლები, ვალიდატორები
│       └── wallet/                     # Wallet Aggregate, ტრანზაქციები, აქტივები
│
├── infrastructure/                     # ინფრასტრუქტურა და გარე სერვისები
│   ├── persistence/
│   │   ├── models/                     # SQLAlchemy ORM მოდელები
│   │   └── repositories/               # რეპოზიტორიების იმპლემენტაცია
│   └── security/                       # Bcrypt ჰეშირებელი, JWT მენეჯერი, სესიები
│
├── services/                           # აპლიკაციის სერვისები (ბიზნეს ოპერაციები)
│   ├── alert_service.py                # ფასის შეტყობინებების მართვა
│   ├── auth_service.py                 # რეგისტრაცია და ლოგინი
│   ├── binance_ws.py                   # Binance WebSocket მენეჯერი
│   ├── market_service.py               # საბაზრო მონაცემები და ფასები
│   ├── order_bot_engine.py             # ფონური სავაჭრო ბოტი
│   ├── order_service.py                # ორდერების მართვა და დარეზერვება
│   ├── user_service.py                 # პროფილის მართვა და სტატისტიკა
│   ├── wallet_service.py               # საფულე, P2P ტრანსფერები, CSV ექსპორტი
│   └── watchlist_service.py            # რჩეული მონეტების მართვა
│
├── presentation/                       # CLI ინტერფეისი (ჩანესტილი მოდულური ხე)
│   ├── auth/
│   │   └── auth_menu.py                # ავტორიზაციის მენიუ
│   ├── admin/
│   │   └── admin_menu.py               # ადმინისტრატორის პანელი
│   └── user/
│       ├── user_menu.py                # მომხმარებლის მთავარი პანელი
│       ├── profile/                    # პროფილის ქვემენიუები
│       │   ├── profile_menu.py
│       │   ├── profile_details_view.py
│       │   ├── account_stats_view.py   # LIVE ანგარიშის სტატისტიკა
│       │   ├── change_password_menu.py
│       │   └── change_username_menu.py
│       ├── wallet/                     # საფულის ქვემენიუები
│       │   ├── wallet_menu.py
│       │   ├── live_wallet_view.py     # LIVE საფულის სტრიმი
│       │   ├── deposit_menu.py
│       │   ├── withdraw_menu.py
│       │   ├── transfer_menu.py        # P2P ტრანსფერი
│       │   ├── transactions_menu.py    # ტრანზაქციები & CSV ექსპორტი
│       │   └── portfolio_analytics_view.py # LIVE პორტფოლიოს ანალიტიკა
│       ├── market/                     # ბაზრის ქვემენიუები
│       │   ├── market_menu.py
│       │   ├── live_market_view.py     # LIVE ბაზრის სტრიმი
│       │   ├── buy_menu.py             # LIVE ყიდვის პრევიუ
│       │   ├── sell_menu.py            # LIVE გაყიდვის პრევიუ
│       │   ├── watchlist/              # LIVE Watchlist მართვა
│       │   ├── alerts/                 # LIVE შეტყობინებების მართვა
│       │   └── movers/                 # LIVE Top Movers
│       └── orders/                     # ორდერების ქვემენიუები
│           ├── orders_menu.py
│           ├── view_orders_menu.py     # LIVE ორდერების სია
│           ├── create_order_menu.py
│           └── cancel_order_menu.py
│
├── alembic/                            # მონაცემთა ბაზის მიგრაციები
├── tests/                              # ავტომატური ტესტები (84 ტესტი)
├── seed_data.py                        # ბაზის გასუფთავება და დემო მონაცემების ჩატვირთვა
└── main.py                             # აპლიკაციის შესასვლელი წერტილი
```

---

## ინსტალაცია და გაშვება

### 1. გარემოს მომზადება
```bash
# ვირტუალური გარემოს შექმნა
python -m venv .venv

# აქტივაცია (Linux/macOS)
source .venv/bin/activate

# აქტივაცია (Windows)
# .venv\Scripts\activate

# დამოკიდებულებების ინსტალაცია
pip install -e .
```

### 2. ბაზის გამართვა (PostgreSQL & Alembic)
დარწმუნდით, რომ `.env` ფაილში მითითებულია PostgreSQL-ის მონაცემები (`DATABASE_URL`).
```bash
alembic upgrade head
```

### 3. სატესტო დემო მონაცემების ჩატვირთვა (Seeder)
ეს ბრძანება ასუფთავებს ბაზას და ქმნის მზა მომხმარებლებს, საფულეებს, აქტივებს, ტრანზაქციებსა და ორდერებს:
```bash
python seed_data.py
```

### 4. აპლიკაციის გაშვება
```bash
python main.py
```

---

## მზა ანგარიშები ტესტირებისთვის

`seed_data.py`-ის გაშვების შემდეგ ხელმისაწვდომია 3 მზა ანგარიში:

| როლი | მომხმარებელი (Username) | პაროლი (Password) | აღწერა |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin` | `Admin123!` | ადმინისტრატორის ანგარიში ($100,000 USD ბალანსით) |
| **Trader** | `trader` | `Trader123!` | ძირითადი მომხმარებელი: $25,000 USD, 0.5 BTC, 4.0 ETH, 25.0 SOL, 3 აქტიური ორდერი, Watchlist და Alerts |
| **P2P User** | `alice` | `Alice123!` | მეორე მომხმარებელი P2P შიდა გადარიცხვების გამოსაცდელად ($5,000 USD, 0.1 BTC) |

---

## ავტომატური ტესტირება

პროექტში რეალიზებულია 84 ავტომატური ტესტი, რომლებიც ფარავს Core ლოგიკას, Domain წესებს, რეპოზიტორიებს, უსაფრთხოებას და ყველა სერვისს:

```bash
pytest
```

შედეგი:
```text
============================== 84 passed in 5.32s ==============================
```

---

## ტექნოლოგიური სტეკი

- **ენა**: Python 3.14
- **მონაცემთა ბაზა**: PostgreSQL
- **ORM & Migrations**: SQLAlchemy 2.0, Alembic
- **ინტერფეისი (CLI)**: Rich (Live rendering, Tables, Panels)
- **რეალური დროის კავშირი**: WebSockets (Binance MiniTicker Stream)
- **უსაფრთხოება**: Bcrypt, PyJWT
- **ტესტირება**: Pytest, Mocking/Monkeypatching
- **არქიტექტურა**: Clean Architecture, Repository Pattern, Result Pattern, Threading (Daemon Background Workers)
