"""Simple Bank Management System: a beginner project for learning OOP in Python.

OOP concepts used:
    - Classes and objects      : Account, SavingsAccount, CurrentAccount, Bank
    - Encapsulation            : the balance is private (__balance), changed only by methods
    - Inheritance              : SavingsAccount and CurrentAccount extend Account
    - Polymorphism             : each account type has its own withdrawal rule
    - Custom exceptions        : InsufficientFundsError

Run:
    python bank.py
"""

from datetime import datetime


class InsufficientFundsError(Exception):
    """Raised when a withdrawal is not allowed."""


# ---------- Account classes ----------

class Account:
    """Base class for every bank account."""

    account_type = "Basic"
    _next_number = 1001          # class attribute shared by all accounts

    def __init__(self, owner, balance=0.0):
        if balance < 0:
            raise ValueError("Opening balance cannot be negative.")
        self.owner = owner
        self.number = Account._next_number
        Account._next_number += 1
        self.__balance = balance        # private: cannot be changed from outside
        self.history = []
        if balance:
            self._log("Opening deposit", balance)

    # Encapsulation: read-only access to the private balance
    @property
    def balance(self):
        return self.__balance

    def _log(self, kind, amount):
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.history.append((stamp, kind, amount, self.__balance))

    def _available(self):
        """Money that can be withdrawn right now. Subclasses override this."""
        return self.__balance

    @staticmethod
    def _check_amount(amount):
        if amount <= 0:
            raise ValueError("Amount must be greater than zero.")

    def deposit(self, amount, kind="Deposit"):
        self._check_amount(amount)
        self.__balance += amount
        self._log(kind, amount)

    def withdraw(self, amount, kind="Withdraw"):
        self._check_amount(amount)
        if amount > self._available():
            raise InsufficientFundsError(
                f"Cannot withdraw {amount:.2f}. Available: {self._available():.2f}"
            )
        self.__balance -= amount
        self._log(kind, amount)

    def statement(self):
        print(f"\nStatement for {self}")
        print(f"{'Date':<20} {'Type':<24} {'Amount':>10} {'Balance':>12}")
        print("-" * 70)
        for stamp, kind, amount, bal in self.history:
            print(f"{stamp:<20} {kind:<24} {amount:>10.2f} {bal:>12.2f}")
        if not self.history:
            print("No transactions yet.")
        print()

    def __str__(self):
        return (f"[{self.number}] {self.account_type:<8} | {self.owner:<15} | "
                f"Balance: {self.balance:.2f}")


class SavingsAccount(Account):
    """Earns interest, but must always keep a minimum balance."""

    account_type = "Savings"
    MIN_BALANCE = 500
    INTEREST_RATE = 4.0          # percent per year

    def __init__(self, owner, balance=0.0):
        if balance < self.MIN_BALANCE:
            raise ValueError(f"Savings account needs at least {self.MIN_BALANCE} to open.")
        super().__init__(owner, balance)

    def _available(self):        # polymorphism: different rule from the base class
        return max(self.balance - self.MIN_BALANCE, 0)

    def add_interest(self):
        interest = round(self.balance * self.INTEREST_RATE / 100 / 12, 2)
        if interest > 0:
            self.deposit(interest, kind="Monthly interest")
        return interest


class CurrentAccount(Account):
    """Can go below zero, up to an overdraft limit."""

    account_type = "Current"
    OVERDRAFT_LIMIT = 5000

    def _available(self):        # polymorphism: balance + overdraft
        return self.balance + self.OVERDRAFT_LIMIT


# ---------- Bank class ----------

class Bank:
    """Holds all accounts and handles operations between them."""

    def __init__(self, name):
        self.name = name
        self.accounts = {}

    def open_account(self, kind, owner, deposit=0.0):
        account_class = {"savings": SavingsAccount, "current": CurrentAccount}[kind]
        account = account_class(owner, deposit)
        self.accounts[account.number] = account
        return account

    def find(self, number):
        if number not in self.accounts:
            raise ValueError(f"No account with number {number}.")
        return self.accounts[number]

    def transfer(self, from_no, to_no, amount):
        if from_no == to_no:
            raise ValueError("Cannot transfer to the same account.")
        source, target = self.find(from_no), self.find(to_no)
        source.withdraw(amount, kind=f"Transfer to {to_no}")
        target.deposit(amount, kind=f"Transfer from {from_no}")

    def add_interest_to_savings(self):
        results = []
        for account in self.accounts.values():
            if isinstance(account, SavingsAccount):
                results.append((account.number, account.add_interest()))
        return results

    def total_deposits(self):
        return sum(a.balance for a in self.accounts.values())


# ---------- Console menu ----------

def ask_int(prompt):
    while True:
        text = input(prompt).strip()
        if text.isdigit():
            return int(text)
        print("  Please enter a whole number.")


def ask_amount(prompt="Amount: "):
    while True:
        try:
            return float(input(prompt).strip())
        except ValueError:
            print("  Please enter a number, e.g. 1500 or 99.50.")


def action_open(bank):
    owner = input("Customer name: ").strip()
    if not owner:
        print("Name cannot be empty.")
        return
    kind = input("Account type (1 = Savings, 2 = Current): ").strip()
    if kind not in ("1", "2"):
        print("Invalid account type.")
        return
    amount = ask_amount("Opening deposit: ")
    account = bank.open_account("savings" if kind == "1" else "current", owner, amount)
    print(f"Account created: {account}")


def action_deposit(bank):
    account = bank.find(ask_int("Account number: "))
    account.deposit(ask_amount())
    print(f"Done. New balance: {account.balance:.2f}")


def action_withdraw(bank):
    account = bank.find(ask_int("Account number: "))
    account.withdraw(ask_amount())
    print(f"Done. New balance: {account.balance:.2f}")


def action_transfer(bank):
    from_no = ask_int("From account number: ")
    to_no = ask_int("To account number: ")
    bank.transfer(from_no, to_no, ask_amount())
    print("Transfer complete.")


def action_statement(bank):
    bank.find(ask_int("Account number: ")).statement()


def action_list(bank):
    if not bank.accounts:
        print("No accounts yet.")
        return
    print()
    for account in bank.accounts.values():
        print(account)
    print(f"\nTotal deposits in {bank.name}: {bank.total_deposits():.2f}")


def action_interest(bank):
    results = bank.add_interest_to_savings()
    if not results:
        print("No savings accounts.")
    for number, interest in results:
        print(f"Account {number}: interest added {interest:.2f}")


MENU = [
    ("Open new account", action_open),
    ("Deposit money", action_deposit),
    ("Withdraw money", action_withdraw),
    ("Transfer money", action_transfer),
    ("Account statement", action_statement),
    ("List all accounts", action_list),
    ("Add monthly interest (savings)", action_interest),
]


def main():
    bank = Bank("Python Bank")
    print(f"=== Welcome to {bank.name} ===")
    while True:
        print()
        for i, (label, _) in enumerate(MENU, 1):
            print(f"  {i}. {label}")
        print("  0. Exit")
        choice = input("Choose: ").strip()
        if choice == "0":
            print("Thank you for banking with us!")
            break
        if choice.isdigit() and 1 <= int(choice) <= len(MENU):
            try:
                MENU[int(choice) - 1][1](bank)
            except (InsufficientFundsError, ValueError) as error:
                print(f"Error: {error}")
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()