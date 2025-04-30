
# Money Manager Discord Bot 

A simple yet powerful Discord bot that helps you track and manage your personal or finances directly from your server. Users can add and view transactions and reports using commands. All data is securely stored in a connected Google Sheet for real-time updates and easy access.


#### 🔗 [Bot Link](https://discord.com/oauth2/authorize?client_id=1366692573577609346&permissions=75776&integration_type=0&scope=bot)


![Logo](https://github.com/user-attachments/assets/fa419321-39ac-43ca-8fb9-385e1a562ecf)


## Features

- 📥 Add income and expenses with different categories
- 📊 View daily, weekly, or monthly summaries
- 🔗 Automatically syncs with Google Sheets
- 📜 View full transaction history by date or categories


## Bot Commands


#### ➕ Add Expense
```
!add <item> <price> [category]
```
Adds a new expense with an optional category.  
**Example:** `!add chai 20 beverage`

---

#### 🤝 Share Sheet
```
!add <item> <price> [category]
```
Adds a new expense with an optional category.  
**Example:** `!share example@gmail.com`

---

#### 📊 Generate Report
```
!report <daily|weekly|monthly>
```

Generates a spending report for the specified period.  
**Example:** `!report weekly`

---

#### 🕓 View History (Last N Entries)
```
!history count <N>
```
Shows the last N expenses logged.  
**Example:** `!history count 5`

---

#### 🗂️ View History by Category
```
!history category <category>
```
Filters and shows history entries by category.  
**Example:** `!history category snacks`

---

#### 📅 View History by Date
```
!history date <YYYY-MM-DD>
```
Shows all entries from the given date.  
**Example:** `!history date 2023-09-15`

---


#### 🆘 Help
```
!helpme
```
Displays the list of available bot commands.


## Tech Stack

**Bot:** Python, discord.py

**Hosting:** Google Cloud Platform (GCP)
## Contributing

Contributions are always welcome!

Please fork this branch and create a pull request for any feature you feel should be added! 
