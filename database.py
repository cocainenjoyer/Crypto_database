import csv
import os
from bisect import bisect_left
from typing import List, Dict, Union, DefaultDict
from collections import defaultdict

CSV_FILE = "data.csv"
BACKUP_FILE = "data_backup.csv"

FIELDS = ["TransactionID", "UserID", "CryptoSymbol", "TransactionType", "Amount"]

class Database:
    def __init__(self, file_path: str = CSV_FILE):
        self.file_path = file_path
        self.data = []
        self.indexes = {"UserID": {}, "CryptoSymbol": {}}  # Hash-based indexes
        if not os.path.exists(self.file_path):
            self._initialize_csv()
        else:
            self._load_data()

    def _initialize_csv(self):
        with open(self.file_path, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=FIELDS)
            writer.writeheader()

    def _load_data(self):
        with open(self.file_path, "r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            self.data = sorted(
                [
                    {
                        "TransactionID": int(row["TransactionID"]),
                        "UserID": int(row["UserID"]),
                        "CryptoSymbol": row["CryptoSymbol"],
                        "TransactionType": row["TransactionType"],
                        "Amount": float(row["Amount"])
                    }
                    for row in reader
                ],
                key=lambda x: x["TransactionID"]
            )
        self._rebuild_indexes()

    def _save_data(self):
        with open(self.file_path, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(self.data)
        self._rebuild_indexes()

    def _rebuild_indexes(self):
        self.indexes = {"UserID": defaultdict(list), "CryptoSymbol": defaultdict(list)}
        for record in self.data:
            for key in self.indexes:
                self.indexes[key][record[key]].append(record)

    def _find_record_index(self, transaction_id: int) -> int:
        keys = [record["TransactionID"] for record in self.data]
        index = bisect_left(keys, transaction_id)
        if index != len(keys) and keys[index] == transaction_id:
            return index
        raise ValueError("TransactionID not found.")

    def create_record(self, record: Dict[str, Union[int, str, float]]) -> bool:
        if any(r["TransactionID"] == record["TransactionID"] for r in self.data):
            raise ValueError("TransactionID must be unique.")
        self.data.append(record)
        self.data.sort(key=lambda x: x["TransactionID"])
        self._save_data()
        return True

    def delete_record(self, key_field: str, value: Union[int, str, float], all_matches: bool = False) -> int:
        if key_field == "TransactionID":
            try:
                index = self._find_record_index(value)
                del self.data[index]
                self._save_data()
                return 1
            except ValueError:
                raise ValueError("TransactionID not found.")
        else:
            records_to_delete = self.indexes.get(key_field, {}).get(value, [])
            if not records_to_delete:
                raise ValueError("No records found matching the criteria.")
            self.data = [r for r in self.data if r not in records_to_delete]
            self._save_data()
            return len(records_to_delete)

    def search_records(self, key_field: str, value: Union[int, str, float]) -> List[Dict[str, Union[int, str, float]]]:
        if key_field in self.indexes:
            return self.indexes[key_field].get(value, [])
        return [r for r in self.data if r[key_field] == value]

    def update_record(self, transaction_id: int, updates: Dict[str, Union[int, str, float]]) -> bool:
        index = self._find_record_index(transaction_id)
        self.data[index].update(updates)
        self._save_data()
        return True

    def backup_database(self):
        with open(self.file_path, "r", encoding="utf-8") as original:
            with open(BACKUP_FILE, "w", encoding="utf-8") as backup:
                backup.write(original.read())

    def restore_from_backup(self):
        if not os.path.exists(BACKUP_FILE):
            raise FileNotFoundError("Backup file not found.")
        with open(BACKUP_FILE, "r", encoding="utf-8") as backup:
            with open(self.file_path, "w", encoding="utf-8") as original:
                original.write(backup.read())
        self._load_data()

    def import_to_excel(self, excel_file: str):
        try:
            from openpyxl import Workbook
        except ImportError:
            raise ImportError("openpyxl is required for this operation.")

        wb = Workbook()
        ws = wb.active
        ws.append(FIELDS)
        for row in self.data:
            ws.append([row[field] for field in FIELDS])
        wb.save(excel_file)
