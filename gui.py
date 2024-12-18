import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from database import Database

class CryptoDBApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Crypto Database Manager")

        self.db = Database()  

        self.create_widgets()

    def create_widgets(self):
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="Create DB", command=self.create_database).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="Load DB", command=self.load_database).grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="Save DB", command=self.db._save_data).grid(row=0, column=2, padx=5)
        ttk.Button(btn_frame, text="Clear DB", command=self.clear_database).grid(row=0, column=3, padx=5)
        ttk.Button(btn_frame, text="Backup DB", command=self.db.backup_database).grid(row=0, column=4, padx=5)
        ttk.Button(btn_frame, text="Restore DB", command=self.restore_database).grid(row=0, column=5, padx=5)
        ttk.Button(btn_frame, text="Delete DB", command=self.delete_database).grid(row=0, column=6, padx=5)
        ttk.Button(btn_frame, text="Exit", command=self.root.quit).grid(row=0, column=7, padx=5)

        record_frame = ttk.Frame(self.root)
        record_frame.pack(pady=10)

        ttk.Button(record_frame, text="Add Record", command=self.add_record).grid(row=0, column=0, padx=5)
        ttk.Button(record_frame, text="Delete Record", command=self.delete_record).grid(row=0, column=1, padx=5)
        ttk.Button(record_frame, text="Search Record", command=self.search_record).grid(row=0, column=2, padx=5)
        ttk.Button(record_frame, text="Edit Record", command=self.edit_record).grid(row=0, column=3, padx=5)
        ttk.Button(record_frame, text="Export to Excel", command=self.export_to_excel).grid(row=0, column=4, padx=5)

        self.tree = ttk.Treeview(
            self.root,
            columns=("TransactionID", "UserID", "CryptoSymbol", "TransactionType", "Amount"),
            show="headings"
        )
        self.tree.pack(fill=tk.BOTH, expand=True, pady=10)

        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)

    def refresh_tree(self):
        """Refresh the treeview with the latest data."""
        for row in self.tree.get_children():
            self.tree.delete(row)
        for record in self.db.data:
            self.tree.insert("", tk.END, values=(
                record["TransactionID"],
                record["UserID"],
                record["CryptoSymbol"],
                record["TransactionType"],
                record["Amount"]
            ))

    def get_user_input(self, title, fields):
        """Prompt user for input for the given fields."""
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

    def create_database(self):
        """Initialize a new database."""
        self.db._initialize_csv()
        self.refresh_tree()
        messagebox.showinfo("Success", "Database created successfully.")

    def load_database(self):
        """Load the database from the CSV file."""
        try:
            self.db._load_data()
            self.refresh_tree()
            messagebox.showinfo("Success", "Database loaded successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load database: {e}")

    def clear_database(self):
        """Clear all records from the database."""
        self.db.data.clear()
        self.refresh_tree()
        messagebox.showinfo("Success", "Database cleared successfully.")

    def restore_database(self):
        """Restore the database from a backup file."""
        try:
            self.db.restore_from_backup()
            self.refresh_tree()
            messagebox.showinfo("Success", "Database restored from backup successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to restore database: {e}")

    def delete_database(self):
        """Delete the entire database."""
        confirm = messagebox.askyesno("Confirm", "Are you sure you want to delete the database?")
        if confirm:
            self.db.delete_database()
            self.refresh_tree()
            messagebox.showinfo("Success", "Database deleted successfully.")

    def add_record(self):
        """Add a new record to the database."""
        fields = ["TransactionID", "UserID", "CryptoSymbol", "TransactionType", "Amount"]
        record = self.get_user_input("Add Record", fields)

        try:
            record["TransactionID"] = int(record["TransactionID"])
            record["UserID"] = int(record["UserID"])
            record["Amount"] = float(record["Amount"])

            self.db.create_record(record)
            self.refresh_tree()
            messagebox.showinfo("Success", "Record added successfully.")
        except ValueError:
            messagebox.showerror("Error", "Invalid input. Please enter valid data types.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add record: {e}")

    def delete_record(self):
        """Delete a record by a field."""
        fields = ["TransactionID", "UserID", "CryptoSymbol", "TransactionType", "Amount"]
        input_data = self.get_user_input("Delete Record", ["Field", "Value"])

        field = input_data["Field"]
        value = input_data["Value"]

        if field not in fields:
            messagebox.showerror("Error", "Invalid field.")
            return

        try:
            if field in ["TransactionID", "UserID"]:
                value = int(value)
            elif field == "Amount":
                value = float(value)

            deleted_count = self.db.delete_record(field, value)
            self.refresh_tree()
            messagebox.showinfo("Success", f"Deleted {deleted_count} record(s) successfully.")
        except ValueError:
            messagebox.showerror("Error", "Invalid value.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete record(s): {e}")

    def edit_record(self):
        """Edit an existing record."""
        transaction_id = self.get_user_input("Edit Record", ["TransactionID"])["TransactionID"]

        try:
            transaction_id = int(transaction_id)
            updates = self.get_user_input("Edit Record", ["UserID", "CryptoSymbol", "TransactionType", "Amount"])
            if "UserID" in updates:
                updates["UserID"] = int(updates["UserID"])
            if "Amount" in updates:
                updates["Amount"] = float(updates["Amount"])

            self.db.update_record(transaction_id, updates)
            self.refresh_tree()
            messagebox.showinfo("Success", "Record updated successfully.")
        except ValueError:
            messagebox.showerror("Error", "Invalid input.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to edit record: {e}")

    def search_record(self):
        """Search for records by a specific field."""
        fields = ["TransactionID", "UserID", "CryptoSymbol", "TransactionType", "Amount"]
        search_input = self.get_user_input("Search Record", ["Field", "Value"])

        field = search_input["Field"]
        value = search_input["Value"]

        if field not in fields:
            messagebox.showerror("Error", "Invalid field.")
            return

        try:
            if field in ["TransactionID", "UserID"]:
                value = int(value)
            elif field == "Amount":
                value = float(value)

            results = self.db.search_records(field, value)
            self.tree.delete(*self.tree.get_children())
            for record in results:
                self.tree.insert("", tk.END, values=(
                    record["TransactionID"],
                    record["UserID"],
                    record["CryptoSymbol"],
                    record["TransactionType"],
                    record["Amount"]
                ))
        except ValueError:
            messagebox.showerror("Error", "Invalid search value.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to search records: {e}")

    def export_to_excel(self):
        """Export the database to an Excel file."""
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
        if file_path:
            try:
                self.db.import_to_excel(file_path)
                messagebox.showinfo("Success", "Database exported to Excel successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export to Excel: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = CryptoDBApp(root)
    root.mainloop()
