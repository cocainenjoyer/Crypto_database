from sortedcontainers import SortedDict
import pickle
import os
import shutil
import openpyxl

class CryptoDatabase:
    def __init__(self, db_file):
        self.db_file = db_file
        self.backup_file = db_file + ".bak"
        self.data = {}  # Основные данные: {TransactionID: {record}}
        self.indexes = {
            'UserID': SortedDict(),
            'CryptoSymbol': SortedDict(),
        }  # Индексы для поиска по UserID и CryptoSymbol

    # Создание новой базы данных
    def create_database(self):
        if os.path.exists(self.db_file):
            print("База данных уже существует.")
            return False
        with open(self.db_file, 'wb') as db:
            pickle.dump({}, db)
        print("База данных успешно создана.")
        return True

    # Удаление базы данных
    def delete_database(self):
        if os.path.exists(self.db_file):
            os.remove(self.db_file)
            print("База данных удалена.")
        else:
            print("База данных не существует.")

    # Очистка базы данных
    def clear_database(self):
        self.data.clear()
        self._rebuild_indexes()
        self.save_database()
        print("База данных очищена.")

    # Открытие базы данных и перестроение индексов
    def open_database(self):
        if not os.path.exists(self.db_file):
            print("База данных отсутствует.")
            return False
        with open(self.db_file, 'rb') as db:
            self.data = pickle.load(db)
        self._rebuild_indexes()
        print("База данных успешно открыта.")
        return True

    # Сохранение базы данных
    def save_database(self):
        with open(self.db_file, 'wb') as db:
            pickle.dump(self.data, db)
        print("База данных успешно сохранена.")

    # Создание backup-файла
    def create_backup(self):
        shutil.copy(self.db_file, self.backup_file)
        print("Резервная копия создана.")

    # Восстановление из backup-файла
    def restore_from_backup(self):
        if not os.path.exists(self.backup_file):
            print("Резервная копия не найдена.")
            return False
        shutil.copy(self.backup_file, self.db_file)
        self.open_database()
        print("База данных восстановлена из резервной копии.")
        return True

    # Перестроение индексов
    def _rebuild_indexes(self):
        self.indexes = {'UserID': SortedDict(), 'CryptoSymbol': SortedDict()}
        for transaction_id, record in self.data.items():
            self._add_to_indexes(transaction_id, record)

    # Добавление записи
    def add_record(self, transaction):
        transaction_id = transaction['TransactionID']
        if transaction_id in self.data:
            print("Ошибка: TransactionID уже существует.")
            return False
        self.data[transaction_id] = transaction
        self._add_to_indexes(transaction_id, transaction)
        print(f"Запись {transaction_id} успешно добавлена.")
        return True

    # Удаление записи
    def delete_record(self, transaction_id):
        if transaction_id in self.data:
            record = self.data.pop(transaction_id)
            self._remove_from_indexes(transaction_id, record)
            print(f"Запись {transaction_id} успешно удалена.")
            return True
        print(f"Запись {transaction_id} не найдена.")
        return False

    # Поиск записей по неключевому полю с использованием индекса
    def search_by_field(self, key, value):
        if key in self.indexes:
            results = self.indexes[key].get(value, [])
            print(f"Найдено {len(results)} записей по {key} = {value}.")
            return [self.data[tid] for tid in results]
        else:
            print(f"Поле {key} не индексировано, линейный поиск...")
            return [record for record in self.data.values() if record.get(key) == value]

    # Удаление записей по неключевому полю
    def delete_by_field(self, key, value):
        records_to_delete = self.search_by_field(key, value)
        for record in records_to_delete:
            self.delete_record(record['TransactionID'])

    # Редактирование записи
    def edit_record(self, transaction_id, updated_record):
        if transaction_id not in self.data:
            print("Запись для редактирования не найдена.")
            return False
        old_record = self.data[transaction_id]
        self._remove_from_indexes(transaction_id, old_record)
        self.data[transaction_id] = updated_record
        self._add_to_indexes(transaction_id, updated_record)
        print(f"Запись {transaction_id} успешно обновлена.")
        return True

    # Импорт базы данных в файл Excel
    def export_to_excel(self, excel_file):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Crypto Transactions"

        # Заголовки
        headers = ["TransactionID", "UserID", "CryptoSymbol", "TransactionType", "Amount", "TransactionDate", "USDValue"]
        ws.append(headers)

        # Данные
        for record in self.data.values():
            ws.append([
                record.get("TransactionID"),
                record.get("UserID"),
                record.get("CryptoSymbol"),
                record.get("TransactionType"),
                record.get("Amount"),
                record.get("TransactionDate"),
                record.get("USDValue")
            ])

        wb.save(excel_file)
        print(f"База данных экспортирована в файл {excel_file}.")

    # Добавление записи в индекс
    def _add_to_indexes(self, transaction_id, record):
        for key in self.indexes:
            if key in record:
                if record[key] not in self.indexes[key]:
                    self.indexes[key][record[key]] = []
                self.indexes[key][record[key]].append(transaction_id)

    # Удаление записи из индекса
    def _remove_from_indexes(self, transaction_id, record):
        for key in self.indexes:
            if key in record:
                if record[key] in self.indexes[key]:
                    self.indexes[key][record[key]].remove(transaction_id)
                    if not self.indexes[key][record[key]]:
                        del self.indexes[key][record[key]]
