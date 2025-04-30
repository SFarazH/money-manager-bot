import discord
from discord.ext import commands
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv
import os
from collections import defaultdict, Counter
from datetime import datetime, timedelta
from discord.errors import Forbidden

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
SERVICE_ACCOUNT_EMAIL = os.getenv("SERVICE_ACCOUNT")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

help_text = (
    "**📘 Available Commands:**\n"
    "🔹 `!add <item> <price> [category]`\n"
    "  ➤ Adds a new expense. Example: `!add chai 20 beverage`\n\n"
    "🔹 `!share <email>`\n"
    "  ➤ Share your Google Sheet with someone.\n\n"
    "🔹 `!report <daily|weekly|monthly>`\n"
    "  ➤ Generates a spending report for a specific period (daily, weekly, or monthly). Example: `!report daily`\n\n"
    "🔹 `!history <count|category|date> <value>`\n"
    "  ➤ View expense history.\n"
    "  ➤ `count`: View the last N number of entries. Example: `!history count 5`\n"
    "  ➤ `category`: View entries for a specific category. Example: `!history category beverage`\n"
    "  ➤ `date`: View entries for a specific date. Example: `!history date 2023-09-15`\n\n"
    "🔹 `!helpme`\n"
    "  ➤ Shows this help message.\n\n"
    "**📘 Created by :** [Faraz](https://github.com/SFarazH)"
)

SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", SCOPE)
client = gspread.authorize(creds)
drive_service = build('drive', 'v3', credentials=creds)


def get_or_create_user_sheet(user_id: str):
    spreadsheet_name = f'moneymanager_{user_id}'

    try:
        print(f'🔍 Checking for existing spreadsheet for user {user_id}...')
        spreadsheet = client.open(spreadsheet_name)
        sheet = spreadsheet.sheet1
        print(f"📝 Sheet Title: {spreadsheet.title}")
    except gspread.exceptions.SpreadsheetNotFound:
        print(f"❌ No sheet found for user {user_id}. Creating new spreadsheet.")
        spreadsheet = client.create(spreadsheet_name)
        sheet = spreadsheet.sheet1
        headings = ["Item", "Price", "Category", "Time"] 
        sheet.insert_row(headings, 1)

    return sheet, spreadsheet_name

#start bot
@bot.event
async def on_ready():
    print(f"🤖 Bot is online as {bot.user}")

@bot.event

# on add welcome message
async def on_guild_join(guild):
    init_text = (
        f"👋 Hello! I'm your Money Manager Bot.\n\n"
        + help_text + "\n\n"
        f"Be sure to run the `!share` command to get access to your sheet!\n\n"
    )

    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).send_messages:
            try:
                await channel.send(init_text)
                break
            except Forbidden:
                continue

    else:
        try:
            await guild.owner.send(
                    f"👋 Thanks for adding me to **{guild.name}**!\n\n"
                    "I couldn't send messages in any channel due to missing permissions.\n"
                    "Please make sure I have permission to send messages in at least one text channel.\n\n"
                    + help_text
            )
        except Exception as e:
            print(f"Failed to DM the guild owner: {e}")


# add expense command
@bot.command(name="add")
async def add_data(ctx, name: str, price: int, category: str = ""):
    """Add an expense entry to the user's Google Sheet."""
    user_id = str(ctx.author.id)
    sheet, spreadsheet_name = get_or_create_user_sheet(user_id)

    try:
        timestamp = datetime.now().strftime("%Y-%m-%d")
        category = category.lower() if category else ""

        row = [timestamp, name, price, category]
        sheet.append_row(row)

        message = f"✅ Added expense: {name} costing {price} {f'in category  {category}' if category else ''} on {timestamp}."            

        await ctx.send(message)
    except Exception as e:
        await ctx.send("❌ Failed to add data.")
        print(f"❌ Error: {e}")


# generate report command
@bot.command(name="report")
async def generate_report(ctx, period: str):
    """Generates a daily, weekly, or monthly spending report."""
    user_id = str(ctx.author.id)
    sheet, spreadsheet_name = get_or_create_user_sheet(user_id)

    try:
        data = sheet.get_all_records()
        now = datetime.now()

        if period == "daily":
            cutoff = now - timedelta(days=1)
        elif period == "weekly":
            cutoff = now - timedelta(weeks=1)
        elif period == "monthly":
            cutoff = now - timedelta(days=30)
        else:
            await ctx.send("❌ Invalid period. Use `daily`, `weekly`, or `monthly`.")
            return

        total_spent = 0
        category_totals = defaultdict(int)
        item_details = []

        for row in data:
            row_time = row.get("Time") or row.get("time") or row.get("Date")
            if not row_time:
                continue
            try:
                entry_date = datetime.strptime(row_time, "%Y-%m-%d")
            except ValueError:
                continue

            if entry_date >= cutoff:
                price = int(row.get("Price", 0))
                category = row.get("Category", "").strip().lower()
                item = row.get("Item", "Unknown")

                total_spent += price
                category_totals[category] += price
                item_details.append((item, price, category))

        if not item_details:
            await ctx.send(f"📊 No entries found in the last {period}.")
            return

        # Highest expense and most frequent category
        highest_item = max(item_details, key=lambda x: x[1])
        category_counts = Counter([x[2] for x in item_details])
        most_common_category = category_counts.most_common(1)[0]

        # Format category summary
        category_breakdown = "\n".join([f"🔸 **{cat or 'uncategorized'}**: {amt}" for cat, amt in category_totals.items()])

        report = (
            f"📅 **{period.capitalize()} Report**\n"
            f"💰 Total Spent: **₹{total_spent}**\n"
            f"📈 Highest Expense: **{highest_item[0]}** (₹{highest_item[1]})\n"
            f"📂 Most Frequent Category: **{most_common_category[0] or 'uncategorized'}** ({most_common_category[1]} times)\n\n"
            f"📊 **Category-wise Breakdown:**\n{category_breakdown}"
        )

        await ctx.send(report)

    except Exception as e:
        print(f"❌ Error generating report: {e}")
        await ctx.send("❌ Failed to generate report.")


# view history command
@bot.command(name="history")
async def view_history(ctx, mode: str = None, *, value: str = None):
    """View expense history by count, category, or date."""
    user_id = str(ctx.author.id)
    sheet, _ = get_or_create_user_sheet(user_id)

    try:
        data = sheet.get_all_records()
        if not data:
            await ctx.send("📭 No expenses found.")
            return

        results = []
        label = ""

        if mode == "count":
            if not value or not value.isdigit():
                await ctx.send("❗ Usage: `!history count <number>`")
                return
            count = int(value)
            results = data[-count:]
            label = f"Last {count} entries"

        elif mode == "category":
            if not value:
                await ctx.send("❗ Usage: `!history category <category>`")
                return
            value = value.lower()
            results = [row for row in data if row.get("Category", "").lower() == value]
            label = f"Entries in category '{value}'"

        elif mode == "date":
            if not value:
                await ctx.send("❗ Usage: `!history date <YYYY-MM-DD>`")
                return
            try:
                search_date = datetime.strptime(value, "%Y-%m-%d").date()
                results = [
                    row for row in data 
                    if datetime.strptime(row.get("Time", ""), "%Y-%m-%d").date() == search_date
                ]
                label = f"Entries on {value}"
            except ValueError:
                await ctx.send("❌ Invalid date format. Use `YYYY-MM-DD`.")
                return

        else:
            await ctx.send("❗ Invalid usage. Try:\n"
                           "`!history count <N>`\n"
                           "`!history category <category>`\n"
                           "`!history date <YYYY-MM-DD>`")
            return

        if not results:
            await ctx.send(f"🔍 No {label.lower()} found.")
            return

        history_text = f"🧾 **Expense History** ({label})\n"
        for row in results:
            date = row.get("Date", "N/A")
            item = row.get("Item", "N/A")
            price = row.get("Price", "N/A")
            category = row.get("Category", "Uncategorized")
            history_text += f"• `{date}` | {item} - ₹{price} [{category}]\n"

        await ctx.send(history_text)

    except Exception as e:
        print(f"❌ Error fetching history: {e}")
        await ctx.send("❌ Failed to retrieve history.")


# share sheet command
@bot.command(name="share")
async def share_sheet(ctx, email: str):
    """Share the user's Google Sheet with another email."""
    user_id = str(ctx.author.id)
    sheet, spreadsheet_name = get_or_create_user_sheet(user_id)
    
    try:
        file_id = sheet.spreadsheet.id  

        print(file_id)

        drive_service.permissions().create(
            fileId=file_id,
            body={'type': 'user', 'role': 'writer', 'emailAddress': email},
            sendNotificationEmail=True
        ).execute()

        await ctx.send(f"✅ Sheet shared with `{email}`.\n" f"🔗 [Click here to open the sheet]({sheet.spreadsheet.url})")
    except HttpError as error:
        await ctx.send("❌ Failed to share the sheet.")
        print(f"❌ Error: {error}")

# help command
@bot.command(name="helpme")
async def help_command(ctx):
    """Display a list of available commands and their usage."""
    await ctx.send(help_text)

# Run the bot
bot.run(BOT_TOKEN)
