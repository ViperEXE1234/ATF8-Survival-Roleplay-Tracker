import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import json
import os

# --- Core Stats ---
food = 100
energy = 100
balance = 0.0
save_file = "savegame.json"
inventory = {}
injuries = {}

# --- Injury System Config ---
limbs = ["Head", "Upper Torso", "Lower Torso", "Left Arm", "Left Hand", "Right Arm", "Right Hand", "Left Leg", "Left Foot", "Right Leg", "Right Foot"]
injury_severity = {
    "Minor": ["Bruise", "Cut", "Stab", "Scratch", "Sprain", "Burn (1st Degree)", "Bleeding"],
    "Serious": ["Bruise", "Deep Cut", "Stab", "Gunwound", "Burn (2nd Degree)", "Fracture", "Broken Bone", "Eletrical Burn", "Bleeding", "Infection"],
    "Major": ["Gunwound", "Severe Burn", "Shattered Bone", "Impaled", "Crushed", "Amputated", "Plasma Burn", "Bleeding", "Internal Bleeding"]
}
injury_buttons = {}

# --- Custom Bars (NEW) ---
custom_bars = {}  # name: { 'value': int, 'rate': int, 'widget': progressbar, 'label': tk.StringVar(), 'name': str }
pause_all = False

# --- Helper Functions ---
def clamp(val): return max(0, min(100, val))

def get_food_status(val):
    if val <= 0: 
        death_screen()
        return "Dead", ""
    elif val < 55: return "Starving", "-1 Combat, -2 Persuasion"
    elif val < 65: return "Hungry", "-1 Combat, -1 Persuasion"
    elif val < 75: return "Peckish", "-1 Combat"
    return "Normal", "No Penalty"

def get_energy_status(val):
    if val <= 0: 
        death_screen()
        return "Dead", ""
    elif val < 55: return "Exhausted", "-3 Combat"
    elif val < 65: return "Tired", "-2 Combat"
    elif val < 75: return "Weary", "-1 Combat"
    return "Normal", "No Penalty"

def update_ui():
    food_bar['value'] = food
    energy_bar['value'] = energy
    fs, fp = get_food_status(food)
    es, ep = get_energy_status(energy)
    food_status_var.set(f"Food Status: {fs} ({fp})")
    energy_status_var.set(f"Energy Status: {es} ({ep})")

    # Update all custom bars UI (NEW)
    for bar in custom_bars.values():
        bar['widget']['value'] = bar['value']
        bar['label'].set(f"{bar['name']} - {bar['value']}%")

def decay():
    global food, energy
    if food > 0: food = clamp(food - 1)
    if energy > 0: energy = clamp(energy - 1)
    update_ui()
    root.after(60000, decay)

def decay_custom_bars():  # NEW
    global pause_all
    if not pause_all:
        for bar in custom_bars.values():
            if bar['value'] > 0:
                bar['value'] = clamp(bar['value'] - bar['rate'])
    update_ui()
    root.after(10000, decay_custom_bars)  # runs every 10 seconds

# --- Injury Management ---
def open_injury_chooser():
    popup = tk.Toplevel(root)
    popup.title("Add Injury")
    for limb in limbs:
        tk.Button(popup, text=limb, command=lambda l=limb: create_injury_button(l, popup)).pack(pady=2)

def create_injury_button(limb, window=None):
    if limb not in injuries:
        injuries[limb] = []

    if limb not in injury_buttons:
        btn = tk.Button(root, text=limb, width=30, command=lambda: show_injuries(limb))
        btn.pack(pady=2)
        injury_buttons[limb] = btn

    if window:
        window.destroy()

def show_injuries(limb):
    popup = tk.Toplevel(root)
    popup.title(f"Injuries - {limb}")

    tk.Label(popup, text=f"Injuries on {limb}:", font=('Arial', 12, 'bold')).pack()
    listbox = tk.Listbox(popup, width=40, height=10)
    listbox.pack()

    for injury in injuries[limb]:
        listbox.insert(tk.END, injury)

    def add_injury():
        severity = simpledialog.askstring("Severity", "Enter severity (Minor, Serious, Major):")
        if not severity or severity.title() not in injury_severity:
            messagebox.showerror("Error", "Invalid severity.")
            return
        severity = severity.title()
        injury = simpledialog.askstring("Injury", f"Choose injury type:\n{', '.join(injury_severity[severity])}")
        if injury:
            full = f"{severity} {injury}"
            injuries[limb].append(full)
            listbox.insert(tk.END, full)

    def delete_injury():
        selected = listbox.curselection()
        if not selected:
            messagebox.showinfo("No Selection", "Please select an injury to delete.")
            return
        index = selected[0]
        confirm = messagebox.askyesno("Confirm", f"Delete injury '{listbox.get(index)}'?")
        if confirm:
            del injuries[limb][index]
            listbox.delete(index)

    btn_frame = tk.Frame(popup)
    btn_frame.pack(pady=5)

    tk.Button(btn_frame, text="➕ Add Injury", command=add_injury).pack(side=tk.LEFT, padx=5)
    tk.Button(btn_frame, text="❌ Delete Selected", command=delete_injury).pack(side=tk.LEFT, padx=5)

# --- Inventory ---
inventory_buttons = {}

def open_inventory_chooser():
    popup = tk.Toplevel(root)
    popup.title("Select Inventory")

    container_options = [
        "Left Lower Pocket", "Right Lower Pocket", "Left Upper Pocket", "Right Lower Pocket", "Belt",
        "Small Backpack", "Medium Backpack", "Large Backpack", "Small Sack", "Large Sack",
        "Small Pouch", "Medium Pouch", "Duffel Bag", "Toolbox", "Chest", "Lootcrate",
        "Small Box", "Med Box", "Large Box", "Cooler", "Fridge", "Vehicle",
        "Drawer", "Small Container", "Large Container", "Misc"
    ]

    for name in container_options:
        tk.Button(popup, text=name, command=lambda n=name: create_inventory_button(n, popup)).pack()

    # Separator and custom option
    tk.Label(popup, text="").pack()
    tk.Button(popup, text="➕ Add Custom", fg="blue", command=lambda: add_custom_inventory(popup)).pack(pady=5)

def create_inventory_button(name, window=None):
    if name not in inventory:
        inventory[name] = []

    if name not in inventory_buttons:
        btn = tk.Button(root, text=name, width=30, command=lambda: show_inventory(name))
        btn.pack(pady=2)
        inventory_buttons[name] = btn

    if window:
        window.destroy()

def add_custom_inventory(popup):
    name = simpledialog.askstring("Custom Inventory", "Enter name for custom storage:")
    if name:
        create_inventory_button(name.strip(), popup)

def show_inventory(name):
    popup = tk.Toplevel(root)
    popup.title(name)

    tk.Label(popup, text=f"Contents of {name}:", font=('Arial', 12, 'bold')).pack()
    listbox = tk.Listbox(popup, width=40, height=10)
    listbox.pack()

    for item in inventory[name]:
        listbox.insert(tk.END, item)

    def add_item():
        item = simpledialog.askstring("Add Item", f"Enter item to add to {name}:")
        if item:
            inventory[name].append(item)
            listbox.insert(tk.END, item)

    def delete_item():
        selected = listbox.curselection()
        if not selected:
            messagebox.showinfo("No Selection", "Please select an item to delete.")
            return
        index = selected[0]
        confirm = messagebox.askyesno("Confirm", f"Delete '{listbox.get(index)}'?")
        if confirm:
            del inventory[name][index]
            listbox.delete(index)

    btn_frame = tk.Frame(popup)
    btn_frame.pack(pady=5)

    tk.Button(btn_frame, text="Add Item", command=add_item).pack(side=tk.LEFT, padx=5)
    tk.Button(btn_frame, text="Delete Selected", command=delete_item).pack(side=tk.LEFT, padx=5)

# --- Save/Load ---
def save_game():
    with open(save_file, 'w') as f:
        json.dump({
            'food': food,
            'energy': energy,
            'inventory': inventory,
            'injuries': injuries,
            'balance': balance,
            'custom_bars': {k: v['value'] for k,v in custom_bars.items()}  # Save bar values
        }, f)
    status_message.set("Game Saved.")

def load_game():
    global food, energy, inventory, injuries, balance
    if os.path.exists(save_file):
        with open(save_file, 'r') as f:
            data = json.load(f)
            food = clamp(data.get('food', 100))
            energy = clamp(data.get('energy', 100))
            inventory = data.get('inventory', {})
            injuries = data.get('injuries', {})
            balance = str(data.get('balance', "0"))

            # Reset buttons before recreating
            for btn in inventory_buttons.values():
                btn.destroy()
            inventory_buttons.clear()

            for btn in injury_buttons.values():
                btn.destroy()
            injury_buttons.clear()

            # Create buttons from loaded data
            for name in inventory:
                create_inventory_button(name)
            for limb in injuries:
                create_injury_button(limb)

            # Load custom bars values (NEW)
            bars_data = data.get('custom_bars', {})
            for name, value in bars_data.items():
                if name in custom_bars:
                    custom_bars[name]['value'] = clamp(value)
                else:
                    # Create bar if missing
                    create_custom_bar(name=name, rate=1, value=clamp(value))  # default decay 1 if rate missing

            update_ui()
            update_balance_display()
            status_message.set("Game Loaded.")

def delete_save():
    global food, energy, inventory, injuries, balance
    if os.path.exists(save_file):
        os.remove(save_file)
    food = 100
    energy = 100
    balance = 0.0
    inventory.clear()
    injuries.clear()
    custom_bars.clear()  # clear custom bars as well
    for btn in inventory_buttons.values():
        btn.destroy()
    for btn in injury_buttons.values():
        btn.destroy()
    inventory_buttons.clear()
    injury_buttons.clear()
    update_ui()
    update_balance_display()
    status_message.set("Save Deleted. All stats reset.")

# --- Food, Drink, Rest ---
def open_food_popup():
    popup = tk.Toplevel(root)
    popup.title("Choose Food")
    tk.Label(popup, text="Low Quality (+15%)", font=('Arial', 10, 'bold')).pack()
    for name in ["Can Of Worms", "Food Paste", "Porridge", "Soup", "Bird", "Insect"]:
        tk.Button(popup, text=name, command=lambda n=name: eat(15, popup)).pack()

    tk.Label(popup, text="Medium Quality (+25%)", font=('Arial', 10, 'bold')).pack()
    for name in ["Fish", "Civ MRE", "Pizza Slice", "Canned Food", "Vegetables"]:
        tk.Button(popup, text=name, command=lambda n=name: eat(25, popup)).pack()

    tk.Label(popup, text="High Quality (+50%)", font=('Arial', 10, 'bold')).pack()
    for name in ["Rat Burger", "Shark Soup", "Mac And Cheese", "Military MRE"]:
        tk.Button(popup, text=name, command=lambda n=name: eat(50, popup)).pack()

def open_drink_popup():
    popup = tk.Toplevel(root)
    popup.title("Choose Drink")
    for name, amount in [("Dirty Water", 10), ("Water", 25), ("Second Sun Soda", 50)]:
        tk.Button(popup, text=name, command=lambda a=amount: rest(a, popup)).pack()

def open_rest_popup():
    popup = tk.Toplevel(root)
    popup.title("Rest Options")
    for name, amount in [("Nap (15%)", 15), ("Rest (40%)", 40), ("Sleep (80%)", 80), ("Deep Sleep (100%)", 100)]:
        tk.Button(popup, text=name, command=lambda a=amount: rest(a if a < 100 else 100, popup)).pack(pady=2)

# --- Stat Actions ---
def eat(amount, window=None):
    global food
    food = clamp(food + amount)
    update_ui()
    if window: window.destroy()

def rest(amount, window=None):
    global energy
    energy = clamp(energy + amount)
    update_ui()
    if window: window.destroy()

def open_mod_menu():
    popup = tk.Toplevel(root)
    popup.title("Utility Menu")
    popup.geometry("250x400")  # Increased height to fit new buttons

    tk.Button(popup, text="Set Energy", command=lambda: set_stat("energy")).pack(pady=5)
    tk.Button(popup, text="Set Food", command=lambda: set_stat("food")).pack(pady=5)
    tk.Button(popup, text="Reset Energy (100)", command=lambda: reset_stat("energy")).pack(pady=5)
    tk.Button(popup, text="Reset Food (100)", command=lambda: reset_stat("food")).pack(pady=5)
    tk.Button(popup, text="Delete All Inventories", command=clear_inventory).pack(pady=5)
    tk.Button(popup, text="☠️ Dead", fg="red", command=death_screen).pack(pady=10)

    # --- NEW BUTTONS ---
    tk.Button(popup, text="➕ Create Bar", command=create_custom_bar).pack(pady=10)
    tk.Button(popup, text="⏸️ Pause All Bars", command=toggle_pause_bars).pack(pady=5)

def set_stat(stat):
    global energy, food
    val = simpledialog.askinteger("Set Value", f"Enter new {stat} value (0-100):")
    if val is not None:
        if stat == "energy": energy = clamp(val)
        elif stat == "food": food = clamp(val)
        update_ui()

def reset_stat(stat):
    global energy, food
    if stat == "energy": energy = 100
    elif stat == "food": food = 100
    update_ui()

def clear_inventory():
    global inventory
    for btn in inventory_buttons.values():
        btn.destroy()
    inventory.clear()
    inventory_buttons.clear()
    status_message.set("Inventory Cleared.")

def death_screen():
    root.destroy()
    death = tk.Tk()
    death.title("Death")
    death.geometry("400x200")
    tk.Label(death, text="☠️ Your Character Has Died ☠️", font=('Arial', 16, 'bold'), fg="red").pack(pady=40)
    tk.Label(death, text="Your journey is over.", font=('Arial', 12)).pack(pady=5)
    death.mainloop()

def set_balance():
    global balance
    val = simpledialog.askstring("Set Balance", "Enter balance (e.g. 6.1 = 6ND 1NC):")
    if val:
        try:
            # Store as string so we can keep trailing zeroes
            balance = val.strip()
            update_balance_display()
        except ValueError:
            messagebox.showerror("Error", "Invalid input.")

def update_balance_display():
    try:
        nd_part, _, nc_part = balance.partition(".")
        nd = int(nd_part) if nd_part else 0
        nc = int(nc_part) if nc_part else 0

        text = f"Balance: {nd}ND"
        if nc > 0:
            text += f" {nc}NC"
        balance_var.set(text)
    except Exception:
        balance_var.set("Balance: INVALID")

# --- Custom Bars Functions (NEW) ---
def create_custom_bar(name=None, rate=None, value=100):
    """
    If called with no args (from UI button), ask user for inputs.
    If called with args (from load_game), create silently.
    """
    if name is None or rate is None:
        try:
            rate = simpledialog.askinteger("Create Bar", "Enter % to decay every 10s (e.g. 10 = -10% per 10s):", minvalue=1, maxvalue=100)
            if rate is None: return

            name = simpledialog.askstring("Bar Name", "Enter name for the new bar:")
            if not name: return
            name = name.strip()

            if name in custom_bars:
                messagebox.showerror("Error", f"A bar named '{name}' already exists.")
                return
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return

    if name in custom_bars:
        # If bar already exists, just update rate and value
        bar = custom_bars[name]
        bar['rate'] = rate
        bar['value'] = value
        update_ui()
        return

    label_var = tk.StringVar()
    bar_frame = tk.Frame(root)
    bar_frame.pack()

    tk.Label(bar_frame, textvariable=label_var).pack()
    bar_widget = ttk.Progressbar(bar_frame, length=300, maximum=100)
    bar_widget.pack(pady=2)

    custom_bars[name] = {
        'name': name,
        'value': value,
        'rate': rate,
        'label': label_var,
        'widget': bar_widget
    }
    update_ui()

def toggle_pause_bars():
    global pause_all
    pause_all = not pause_all
    status_message.set("Bars Paused" if pause_all else "Bars Resumed")

# --- UI Setup ---
root = tk.Tk()
root.title("Survival Tracker")
root.geometry("450x780")

food_status_var = tk.StringVar()
energy_status_var = tk.StringVar()
status_message = tk.StringVar()

tk.Label(root, text="Food").pack()
food_bar = ttk.Progressbar(root, length=300, maximum=100)
food_bar.pack(pady=5)

tk.Label(root, text="Energy").pack()
energy_bar = ttk.Progressbar(root, length=300, maximum=100)
energy_bar.pack(pady=5)

tk.Label(root, textvariable=food_status_var, font=('Arial', 12)).pack(pady=5)
tk.Label(root, textvariable=energy_status_var, font=('Arial', 12)).pack(pady=5)
balance_var = tk.StringVar(value="Balance: 0ND")

tk.Button(root, text="🍽️ Eat", command=open_food_popup, width=30).pack(pady=2)
tk.Button(root, text="🥤 Drink", command=open_drink_popup, width=30).pack(pady=2)
tk.Button(root, text="🛌 Rest", command=open_rest_popup, width=30).pack(pady=2)
balance_label = tk.Label(root, textvariable=balance_var, anchor='e', font=('Arial', 10, 'bold'))
balance_label.place(relx=0.98, rely=0.975, anchor='se')
balance_note = tk.Label(root, text="Decimal = NC (e.g. 6.1 → 6ND 1NC)", font=('Arial', 8), fg="gray")
balance_note.place(relx=0.98, rely=0.94, anchor='se')
tk.Button(root, text="💰 Balance", command=set_balance, width=30).pack(pady=2)

tk.Button(root, text="➕ Add Inventory", command=open_inventory_chooser, width=30).pack(pady=10)
tk.Button(root, text="🩹 Add Injury", command=open_injury_chooser, width=30).pack(pady=2)
tk.Button(root, text="⚙️ Utility Menu", command=open_mod_menu, width=30).pack(pady=10)

tk.Button(root, text="💾 Save Game", command=save_game).pack(pady=5)
tk.Button(root, text="📂 Load Game", command=load_game).pack(pady=5)
tk.Button(root, text="🗑️ Delete Save", command=delete_save).pack(pady=5)

tk.Label(root, textvariable=status_message, fg="green").pack(pady=5)

load_game()
update_ui()

root.after(60000, decay)
root.after(10000, decay_custom_bars)  # Start the custom bars decay loop

root.mainloop()