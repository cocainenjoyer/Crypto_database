# File: gui_manager.py

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from crypto_database import CryptoDatabase


class CryptoDBApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Crypto Database Manager")

        self.db = CryptoDatabase("crypto_db.pkl")

        self.create_widgets()

    def create_widgets(self):
        # Buttons for DB operations
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="Create DB", command=self.db.create_database).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="Open DB", command=self.open_database).grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="Save DB", command=self.db.save_database).grid(row=0, column=2, padx=5)
        ttk.Button(btn_frame, text="Clear DB", command=self.db.clear_database).grid(row=0, column=3, padx=5)
        ttk.Button(btn_frame, text="Backup DB", command=self.db.create_backup).grid(row=0, column=4, padx=5)
        ttk.Button(btn_frame, text="Restore DB", command=self.db.restore_from_backup).grid(row=0, column=5, padx=5)
        ttk.Button(btn_frame, text="Delete DB", command=self.delete_database).grid(row=0, column=6, padx=5)

        record_frame = ttk.Frame(self.root)
        record_frame.pack(pady=10)

        ttk.Button(record_frame, text="Add Record", command=self.add_record).grid(row=0, column=0, padx=5)
        ttk.Button(record_frame, text="Delete Record", command=self.delete_record).grid(row=0, column=1, padx=5)
        ttk.Button(record_frame, text="Edit Record", command=self.edit_record).grid(row=0, column=2, padx=5)
        ttk.Button(record_frame, text="Search Record", command=self.search_record).grid(row=0, column=3, padx=5)
        ttk.Button(record_frame, text="Export to Excel", command=self.export_to_excel).grid(row=0, column=4, padx=5)
        ttk.Button(record_frame, text="Delete by Field", command=self.delete_by_field).grid(row=0, column=5, padx=5)

        self.tree = ttk.Treeview(
            self.root,
            columns=("TransactionID", "UserID", "CryptoSymbol", "TransactionType", "Amount", "TransactionDate", "USDValue"),
            show="headings"
        )
        self.tree.pack(fill=tk.BOTH, expand=True, pady=10)

        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)

    def open_database(self):
        if self.db.open_database():
            self.refresh_tree()

    def refresh_tree(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for record in self.db.data.values():
            self.tree.insert("", tk.END, values=(
                record["TransactionID"],
                record["UserID"],
                record["CryptoSymbol"],
                record["TransactionType"],
                record["Amount"],
                record["TransactionDate"],
                record["USDValue"]
            ))

    def get_user_input(self, title, fields):
        input_window = tk.Toplevel(self.root)
        input_window.title(title)

        entries = {}

        for i, field in enumerate(fields):
            ttk.Label(input_window, text=field).grid(row=i, column=0, padx=10, pady=5, sticky=tk.W)
            entry = ttk.Entry(input_window)
            entry.grid(row=i, column=1, padx=10, pady=5)
            entries[field] = entry

        def on_submit():
            self.user_input = {field: entries[field].get() for field in fields}
            input_window.destroy()

        ttk.Button(input_window, text="Submit", command=on_submit).grid(row=len(fields), column=0, columnspan=2, pady=10)

        input_window.grab_set()
        self.root.wait_window(input_window)
        return self.user_input

    def get_record_from_user(self):
        fields = ["TransactionID", "UserID", "CryptoSymbol", "TransactionType", "Amount", "TransactionDate", "USDValue"]
        record = self.get_user_input("Add/Edit Record", fields)

        # Convert fields to appropriate types
        try:
            record["TransactionID"] = int(record["TransactionID"])
            record["UserID"] = int(record["UserID"])
            record["Amount"] = float(record["Amount"])
            record["USDValue"] = float(record["USDValue"])
        except ValueError:
            messagebox.showerror("Input Error", "Invalid numeric values.")
            return None

        return record

    def add_record(self):
        record = self.get_record_from_user()
        if record and self.db.add_record(record):
            self.refresh_tree()

    def delete_record(self):
        transaction_id = self.get_user_input("Delete Record", ["TransactionID"])["TransactionID"]
        if self.db.delete_record(int(transaction_id)):
            self.refresh_tree()

    def edit_record(self):
        transaction_id = self.get_user_input("Edit Record", ["TransactionID"])["TransactionID"]
        if not transaction_id.isdigit() or int(transaction_id) not in self.db.data:
            messagebox.showerror("Error", "TransactionID not found.")
            return

        record = self.get_record_from_user()
        if record and self.db.edit_record(int(transaction_id), record):
            self.refresh_tree()

    def search_record(self):
        key = self.get_user_input("Search Record", ["Field"])["Field"]
        value = self.get_user_input("Search Record", ["Value"])["Value"]

        if key not in ["TransactionID", "UserID", "CryptoSymbol", "TransactionType", "Amount", "TransactionDate", "USDValue"]:
            messagebox.showerror("Error", "Invalid field.")
            return

        results = self.db.search_by_field(key, value if key in ["CryptoSymbol", "TransactionType"] else int(value))

        if results:
            for row in self.tree.get_children():
                self.tree.delete(row)
            for record in results:
                self.tree.insert("", tk.END, values=(
                    record["TransactionID"],
                    record["UserID"],
                    record["CryptoSymbol"],
                    record["TransactionType"],
                    record["Amount"],
                    record["TransactionDate"],
                    record["USDValue"]
                ))
        else:
            messagebox.showinfo("Search Results", "No records found.")

    def delete_by_field(self):
        # Prompt user for field and value
        user_input = self.get_user_input("Delete by Field", ["Field", "Value"])
        field = user_input.get("Field")
        value = user_input.get("Value")

        if field not in ["TransactionID", "UserID", "CryptoSymbol", "TransactionType", "Amount", "TransactionDate", "USDValue"]:
            messagebox.showerror("Error", "Invalid field.")
            return

        try:
            if field in ["TransactionID", "UserID"]:
                value = int(value)
            elif field in ["Amount", "USDValue"]:
                value = float(value)
        except ValueError:
            messagebox.showerror("Error", f"Value for field {field} must be numeric.")
            return

        self.db.delete_by_field(field, value)
        self.refresh_tree()

    def delete_database(self):
        confirmation = messagebox.askyesno("Delete Database", "Are you sure you want to delete the database?")
        if confirmation:
            self.db.delete_database()
            self.refresh_tree()

    def export_to_excel(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
        if file_path:
            self.db.export_to_excel(file_path)


if __name__ == "__main__":
    root = tk.Tk()
    app = CryptoDBApp(root)
    root.mainloop()
