import asyncio
import re
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from timeit import default_timer
import pandas as pd
import requests
from plyer import notification
import tkinter as tk
from tkinter import ttk

op = os.name == 'nt'
if op: import winsound

c = requests.get("https://api.hypixel.net/skyblock/auctions?page=0")
resp = c.json()
now = resp['lastUpdated']
toppage = resp['totalPages']

results = []
prices = {}
fetching = False

REFORGES = [" ✦", "⚚ ", " ✪", "✪", "Stiff ", "Lucky ", "Jerry's ", "Dirty ", "Fabled ", "Suspicious ", "Gilded ", "Warped ", "Withered ", "Bulky ", "Stellar ", "Heated ", "Ambered ", "Fruitful ", "Magnetic ", "Fleet ", "Mithraic ", "Auspicious ", "Refined ", "Headstrong ", "Precise ", "Spiritual ", "Moil ", "Blessed ", "Toil ", "Bountiful ", "Candied ", "Submerged ", "Reinforced ", "Cubic ", "Warped ", "Undead ", "Ridiculous ", "Necrotic ", "Spiked ", "Jaded ", "Loving ", "Perfect ", "Renowned ", "Giant ", "Empowered ", "Ancient ", "Sweet ", "Silky ", "Bloody ", "Shaded ", "Gentle ", "Odd ", "Fast ", "Fair ", "Epic ", "Sharp ", "Heroic ", "Spicy ", "Legendary ", "Deadly ", "Fine ", "Grand ", "Hasty ", "Neat ", "Rapid ", "Unreal ", "Awkward ", "Rich ", "Clean ", "Fierce ", "Heavy ", "Light ", "Mythic ", "Pure ", "Smart ", "Titanic ", "Wise ", "Bizarre ", "Itchy ", "Ominous ", "Pleasant ", "Pretty ", "Shiny ", "Simple ", "Strange ", "Vivid ", "Godly ", "Demonic ", "Forceful ", "Hurtful ", "Keen ", "Strong ", "Superior ", "Unpleasant ", "Zealous "]

LOWEST_PRICE = 5
NOTIFY = False
LOWEST_PERCENT_MARGIN = 1/2
START_TIME = default_timer()

def fetch(session, page):
    global toppage
    base_url = "https://api.hypixel.net/skyblock/auctions?page="
    with session.get(base_url + page) as response:
        data = response.json()
        toppage = data['totalPages']
        if data['success']:
            for auction in data['auctions']:
                if not auction['claimed'] and auction['bin'] == True and not "Furniture" in auction["item_lore"]:
                    index = re.sub("\[[^\]]*\]", "", auction['item_name']) + auction['tier']
                    for reforge in REFORGES: index = index.replace(reforge, "")
                    if index in prices:
                        if prices[index][0] > auction['starting_bid']:
                            prices[index][1] = prices[index][0]
                            prices[index][0] = auction['starting_bid']
                        elif prices[index][1] > auction['starting_bid']:
                            prices[index][1] = auction['starting_bid']
                    else:
                        prices[index] = [auction['starting_bid'], float("inf")]
                    if prices[index][1] > LOWEST_PRICE and prices[index][0]/prices[index][1] < LOWEST_PERCENT_MARGIN and auction['start']+60000 > now:
                        results.append([auction['uuid'], auction['item_name'], auction['starting_bid'], index])
        return data

async def get_data_asynchronous():
    pages = [str(x) for x in range(toppage)]
    with ThreadPoolExecutor(max_workers=50) as executor:
        with requests.Session() as session:
            loop = asyncio.get_event_loop()
            START_TIME = default_timer()
            tasks = [
                loop.run_in_executor(
                    executor,
                    fetch,
                    *(session, page)
                )
                for page in pages if int(page) < toppage
            ]
            for response in await asyncio.gather(*tasks):
                pass

def main():
    global results, prices, START_TIME, fetching
    START_TIME = default_timer()
    results = []
    prices = {}
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    future = asyncio.ensure_future(get_data_asynchronous())
    loop.run_until_complete(future)
    
    if len(results): results = [[entry, prices[entry[3]][1]] for entry in results if (entry[2] > LOWEST_PRICE and prices[entry[3]][1] != float('inf') and prices[entry[3]][0] == entry[2] and prices[entry[3]][0]/prices[entry[3]][1] < LOWEST_PERCENT_MARGIN)]
    
    if len(results):
        if NOTIFY: 
            notification.notify(
                title = max(results, key=lambda entry:entry[1])[0][1],
                message = "Lowest BIN: " + f'{max(results, key=lambda entry:entry[1])[0][2]:,}' + "\nSecond Lowest: " + f'{max(results, key=lambda entry:entry[1])[1]:,}',
                app_icon = None,
                timeout = 4,
            )
        
        df=pd.DataFrame(['/viewauction ' + str(max(results, key=lambda entry:entry[1])[0][0])])
        df.to_clipboard(index=False,header=False)
        
        done = default_timer() - START_TIME
        if op: winsound.Beep(500, 500)
        for result in results:
            profit_percent = ((result[1] - result[0][2]) / result[1]) * 100
            tree.insert("", tk.END, values=(result[0][0], result[0][1], f'{result[0][2]:,}', f'{result[1]:,}', f'{profit_percent:.2f}%', round(done, 2)))
    fetching = False
    status_label.config(text="Status: Idle")

def dostuff():
    global now, toppage, fetching
    while fetching:
        if time.time()*1000 > now + 60000:
            prevnow = now
            now = float('inf')
            c = requests.get("https://api.hypixel.net/skyblock/auctions?page=0").json()
            if c['lastUpdated'] != prevnow:
                now = c['lastUpdated']
                toppage = c['totalPages']
                main()
            else:
                now = prevnow
        time.sleep(0.25)

def start_fetching():
    global fetching
    if not fetching:
        fetching = True
        status_label.config(text="Status: Fetching...")
        threading.Thread(target=dostuff, daemon=True).start()

def stop_fetching():
    global fetching
    fetching = False
    status_label.config(text="Status: Stopped")

def copy_command():
    if results:
        command = '/viewauction ' + str(max(results, key=lambda entry:entry[1])[0][0])
        root.clipboard_clear()
        root.clipboard_append(command)
        root.update()

def clear_results():
    for item in tree.get_children():
        tree.delete(item)

root = tk.Tk()
root.title("Hypixel AH Snipper")
root.geometry("1200x800")


top_frame = tk.Frame(root)
top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

middle_frame = tk.Frame(root)
middle_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)

bottom_frame = tk.Frame(root)
bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)


search_label = tk.Label(top_frame, text="Search Item:")
search_label.pack(side=tk.LEFT, padx=5)
search_entry = tk.Entry(top_frame)
search_entry.pack(side=tk.LEFT, padx=5)


start_button = tk.Button(top_frame, text="Start Fetching", command=start_fetching)
start_button.pack(side=tk.LEFT, padx=5)

stop_button = tk.Button(top_frame, text="Stop Fetching", command=stop_fetching)
stop_button.pack(side=tk.LEFT, padx=5)

copy_button = tk.Button(top_frame, text="Copy Auction Command", command=copy_command)
copy_button.pack(side=tk.LEFT, padx=5)

clear_button = tk.Button(top_frame, text="Clear Results", command=clear_results)
clear_button.pack(side=tk.LEFT, padx=5)


status_label = tk.Label(bottom_frame, text="Status: Idle", anchor=tk.W)
status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

columns = ("UUID", "Item Name", "Item Price", "Second Lowest BIN", "Profit (%)", "Time to Refresh AH")
tree = ttk.Treeview(middle_frame, columns=columns, show="headings")
for col in columns:
    tree.heading(col, text=col)
tree.pack(pady=20, fill=tk.BOTH, expand=True)

root.mainloop()