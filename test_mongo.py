from db_connector import connect_to_mongo

if __name__ == "__main__":
    data = connect_to_mongo()
    print("📊 داده‌های دریافت شده از دیتابیس:")
    for row in data:
        print(row)
