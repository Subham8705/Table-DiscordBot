import discord
from discord.ext import commands
from tabulate import tabulate
from dotenv import load_dotenv
import os, json
import shlex
from keep_alive import keep_alive

keep_alive()

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# === Load & Save Table Functions ===
DATA_FILE = "tables.json"


def load_tables():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}


def save_tables():
    with open(DATA_FILE, "w") as f:
        json.dump(tables, f, indent=2)


tables = load_tables()

# === Commands ===


@bot.command()
async def newtable(ctx, tablename):
    guild_id = str(ctx.guild.id)
    if guild_id not in tables:
        tables[guild_id] = {}
    if tablename in tables[guild_id]:
        await ctx.send("Table already exists!")
    else:
        tables[guild_id][tablename] = {"columns": [], "rows": []}
        save_tables()
        await ctx.send(f"Table '{tablename}' created.")


@bot.command()
async def addcol(ctx, tablename, *, colname):
    guild_id = str(ctx.guild.id)
    if guild_id not in tables or tablename not in tables[guild_id]:
        return await ctx.send("Table not found.")
    tables[guild_id][tablename]["columns"].append(colname)
    for row in tables[guild_id][tablename]["rows"]:
        row.append("")
    save_tables()
    await ctx.send(f"Column '{colname}' added to '{tablename}'.")


@bot.command()
async def addrow(ctx, tablename, *, row_data):
    guild_id = str(ctx.guild.id)
    if guild_id not in tables or tablename not in tables[guild_id]:
        return await ctx.send("Table not found.")

    try:
        values = shlex.split(row_data)
    except ValueError:
        return await ctx.send(
            "❌ Error parsing row. Use quotes for multi-word entries.")

    expected = len(tables[guild_id][tablename]["columns"])
    if len(values) != expected:
        return await ctx.send(
            f"❌ Expected {expected} values, but got {len(values)}.")

    tables[guild_id][tablename]["rows"].append(values)
    save_tables()
    await ctx.send(f"✅ Row added to '{tablename}'.")


@bot.command()
async def showtable(ctx, tablename):
    guild_id = str(ctx.guild.id)
    if guild_id not in tables or tablename not in tables[guild_id]:
        return await ctx.send("Table not found.")

    table = tables[guild_id][tablename]
    cols = table["columns"]
    rows = table["rows"]

    if not cols:
        return await ctx.send("No columns in this table.")

    rows_per_page = 20
    total_pages = max(1, (len(rows) + rows_per_page - 1) // rows_per_page)

    def get_page(page):
        start = (page - 1) * rows_per_page
        end = start + rows_per_page
        page_rows = rows[start:end]
        table_str = tabulate(page_rows, headers=cols, tablefmt="github")
        return f"📄 **{tablename}** — Page {page}/{total_pages}\n```{table_str}```"

    current_page = 1
    message = await ctx.send(get_page(current_page))

    if total_pages == 1:
        return  # no need for pagination

    await message.add_reaction("⬅️")
    await message.add_reaction("➡️")

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in ["⬅️", "➡️"] and reaction.message.id == message.id

    while True:
        try:
            reaction, user = await bot.wait_for("reaction_add", timeout=60.0, check=check)

            if str(reaction.emoji) == "➡️" and current_page < total_pages:
                current_page += 1
            elif str(reaction.emoji) == "⬅️" and current_page > 1:
                current_page -= 1
            else:
                await message.remove_reaction(reaction, user)
                continue

            await message.edit(content=get_page(current_page))
            await message.remove_reaction(reaction, user)

        except Exception:
            break 



@bot.command()
async def delrow(ctx, tablename, index: int):
    guild_id = str(ctx.guild.id)
    if guild_id not in tables or tablename not in tables[guild_id]:
        return await ctx.send("Table not found.")
    if index < 1 or index > len(tables[guild_id][tablename]["rows"]):
        return await ctx.send("Invalid row number.")
    removed = tables[guild_id][tablename]["rows"].pop(index - 1)
    save_tables()
    await ctx.send(f"Deleted row {index}: {removed}")


@bot.command()
async def delcol(ctx, tablename, *, colname):
    guild_id = str(ctx.guild.id)
    if guild_id not in tables or tablename not in tables[guild_id]:
        return await ctx.send("Table not found.")
    cols = tables[guild_id][tablename]["columns"]
    if colname not in cols:
        return await ctx.send(f"Column '{colname}' not found.")
    col_index = cols.index(colname)
    tables[guild_id][tablename]["columns"].pop(col_index)
    for row in tables[guild_id][tablename]["rows"]:
        if len(row) > col_index:
            row.pop(col_index)
    save_tables()
    await ctx.send(f"Deleted column '{colname}'.")


@bot.command()
async def commands(ctx):
    embed = discord.Embed(title="📋 Table Bot Commands",
                          color=discord.Color.blurple())
    embed.add_field(name="!newtable <name>",
                    value="Create a new table",
                    inline=False)
    embed.add_field(name="!addcol <table> <column_name>",
                    value="Add a column",
                    inline=False)
    embed.add_field(
        name="!addrow <table> <val1> <val2> ...",
        value=
        'Add a row. \nUse "quotes" for spaces. Example: !addrow students "Alice Smith" 20',
        inline=False)
    embed.add_field(name="!showtable <table>",
                    value="Show the table",
                    inline=False)
    embed.add_field(name="!editcell <table> <row> <col> <value>",
                    value="Edit a specific cell",
                    inline=False)
    embed.add_field(name="!editrow <table> <row> <val1> <val2> ...",
                    value="Edit an entire row",
                    inline=False)
    embed.add_field(name="!editcol <table> <old_col> <new_col>",
                    value="Rename a column",
                    inline=False)
    embed.add_field(name="!cleartable <table>",
                    value="Clear all rows (keep columns)",
                    inline=False)
    embed.add_field(name="!delrow <table> <row_number>",
                    value="Delete a row",
                    inline=False)
    embed.add_field(name="!delcol <table> <column_name>",
                    value="Delete a column",
                    inline=False)
    embed.add_field(name="!viewtable",
                    value="View list of your server's tables",
                    inline=False)
    embed.add_field(name="!deletetable <table>",
                    value="Delete the entire table",
                    inline=False)

    embed.set_footer(text="🤖 Bot created by PRORAPIOR")

    await ctx.send(embed=embed)


@bot.command()
async def viewtable(ctx):
    guild_id = str(ctx.guild.id)
    if guild_id not in tables or not tables[guild_id]:
        await ctx.send("🚫 No tables found.")
        return
    table_list = "\n".join(f"- `{name}`" for name in tables[guild_id].keys())
    await ctx.send(f"📄 **Available Tables in This Server:**\n{table_list}")


@bot.command()
async def editcell(ctx, tablename, row: int, column: str, *, new_value):
    guild_id = str(ctx.guild.id)
    if guild_id not in tables or tablename not in tables[guild_id]:
        return await ctx.send("Table not found.")

    table = tables[guild_id][tablename]
    if column not in table["columns"]:
        return await ctx.send(f"Column '{column}' not found.")

    if row < 1 or row > len(table["rows"]):
        return await ctx.send("Invalid row number.")

    col_index = table["columns"].index(column)
    tables[guild_id][tablename]["rows"][row - 1][col_index] = new_value
    save_tables()
    await ctx.send(f"Updated `{column}` in row {row} to `{new_value}`.")


@bot.command()
async def editrow(ctx, tablename, row: int, *values):
    guild_id = str(ctx.guild.id)
    if guild_id not in tables or tablename not in tables[guild_id]:
        return await ctx.send("Table not found.")

    table = tables[guild_id][tablename]
    if row < 1 or row > len(table["rows"]):
        return await ctx.send("Invalid row number.")

    if len(values) != len(table["columns"]):
        return await ctx.send(f"Expected {len(table['columns'])} values.")

    table["rows"][row - 1] = list(values)
    save_tables()
    await ctx.send(f"Row {row} updated successfully.")


@bot.command()
async def editcol(ctx, tablename, old_col: str, new_col: str):
    guild_id = str(ctx.guild.id)
    if guild_id not in tables or tablename not in tables[guild_id]:
        return await ctx.send("Table not found.")

    table = tables[guild_id][tablename]
    if old_col not in table["columns"]:
        return await ctx.send(f"Column '{old_col}' not found.")

    col_index = table["columns"].index(old_col)
    table["columns"][col_index] = new_col
    save_tables()
    await ctx.send(f"Renamed column '{old_col}' to '{new_col}'.")


@bot.command()
async def cleartable(ctx, tablename):
    guild_id = str(ctx.guild.id)
    if guild_id not in tables or tablename not in tables[guild_id]:
        return await ctx.send("Table not found.")

    tables[guild_id][tablename]["rows"] = []
    save_tables()
    await ctx.send(f"✅ All rows in '{tablename}' have been cleared.")


@bot.command()
async def deletetable(ctx, tablename):
    guild_id = str(ctx.guild.id)
    if guild_id not in tables or tablename not in tables[guild_id]:
        return await ctx.send("Table not found.")

    confirm_msg = await ctx.send(
        f"⚠️ Are you sure you want to permanently delete the table `{tablename}`?\nReact with ✅ to confirm or ❌ to cancel."
    )
    await confirm_msg.add_reaction("✅")
    await confirm_msg.add_reaction("❌")

    def check(reaction, user):
        return (user == ctx.author and str(reaction.emoji) in ["✅", "❌"]
                and reaction.message.id == confirm_msg.id)

    try:
        reaction, user = await bot.wait_for("reaction_add",
                                            timeout=30.0,
                                            check=check)
        if str(reaction.emoji) == "✅":
            del tables[guild_id][tablename]
            save_tables()
            await ctx.send(f"🗑️ Table `{tablename}` has been deleted.")
        else:
            await ctx.send("❌ Deletion cancelled.")
    except:
        await ctx.send("⌛ Confirmation timed out. Table not deleted.")

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name="Use !commands"))


bot.run(TOKEN)
