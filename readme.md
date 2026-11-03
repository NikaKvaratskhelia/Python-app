finance_cli/
│
├── domain/                    # 🟢 ბიზნესის გული (არ იცის ბაზაზე, CLI-ზე ან ფრეიმვორკებზე)
│   ├── entities/              # Rich Domain Models (User, Transaction, Asset)
│   ├── value_objects/         # Value Objects (Money, Email, Category)
│   └── exceptions.py          # ბიზნეს ლოგიკის შეცდომები (InsufficientFundsError და ა.შ.)
│
├── application/               # 🟡 აპლიკაციის სერვისები / Use Cases (ორკესტრაცია)
│   ├── services/              # AuthUseCase, TransactionUseCase
│   └── interfaces/            # Repository კონტრაქტები (Abstract Base Classes)
│
├── infrastructure/            # 🔴 გარე სამყარო და ინფრასტრუქტურა
│   ├── persistence/           # SQLAlchemy მოდელები და Repository იმპლემენტაციები
│   └── security/              # Bcrypt, JWT გენერაცია
│
├── presentation/              # 🔵 იუზერთან ურთიერთობა (CLI მენიუები)
│   └── menus/                 # Questionary / Typer ინტერაქტიული ეკრანები
│
├── core/                      # კონფიგურაცია და გლობალური პარამეტრები (.env, database engine)
└── main.py                    # აპლიკაციის შესასვლელი წერტილი