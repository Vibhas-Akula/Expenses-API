from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

# Initialize the database
def init_db():
    with sqlite3.connect('new.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS groups (
                          group_id INTEGER PRIMARY KEY, 
                          group_name TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                          user_id INTEGER PRIMARY KEY, 
                          name TEXT, 
                          group_id INTEGER, 
                          FOREIGN KEY (group_id) REFERENCES groups(group_id))''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS expenses (
                          expense_id INTEGER PRIMARY KEY, 
                          description TEXT, 
                          amount REAL, 
                          paid_by INTEGER, 
                          group_id INTEGER, 
                          FOREIGN KEY (paid_by) REFERENCES users(user_id),
                          FOREIGN KEY (group_id) REFERENCES groups(group_id))''')
        conn.commit()

# Insert sample data (for testing purposes)
def insert_sample_data():
    with sqlite3.connect('new.db') as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO groups (group_name) VALUES (?)', ('Friends Group',))
        group_id = cursor.lastrowid
        cursor.execute('INSERT INTO users (name, group_id) VALUES (?, ?)', ('Alice', group_id))
        cursor.execute('INSERT INTO users (name, group_id) VALUES (?, ?)', ('Bob', group_id))
        cursor.execute('INSERT INTO users (name, group_id) VALUES (?, ?)', ('Charlie', group_id))
        cursor.execute('INSERT INTO expenses (description, amount, paid_by, group_id) VALUES (?, ?, ?, ?)', 
                       ('Dinner', 200.0, 1, group_id))
        cursor.execute('INSERT INTO expenses (description, amount, paid_by, group_id) VALUES (?, ?, ?, ?)', 
                       ('Lunch', 150.0, 2, group_id))
        conn.commit()

@app.route('/add_expense', methods=['POST'])
def add_expense():
    try:
        data = request.get_json()
        description = data.get('description')
        amount = data.get('amount')
        paid_by = data.get('paid_by')
        group_id = data.get('group_id')

        # Validate input data
        if not description or amount <= 0:
            return jsonify({'error': 'Invalid input data'}), 400

        with sqlite3.connect('new.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE user_id = ? AND group_id = ?', (paid_by, group_id))
            user = cursor.fetchone()
            if not user:
                return jsonify({'error': 'User not found in the specified group'}), 404

            cursor.execute('INSERT INTO expenses (description, amount, paid_by, group_id) VALUES (?, ?, ?, ?)', 
                           (description, amount, paid_by, group_id))
            conn.commit()
        return jsonify({'message': 'Expense added successfully'}), 200
    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_group/<int:group_id>', methods=['GET'])
def get_group(group_id):
    try:
        with sqlite3.connect('new.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM groups WHERE group_id = ?', (group_id,))
            group = cursor.fetchone()
            cursor.execute('SELECT * FROM users WHERE group_id = ?', (group_id,))
            users = cursor.fetchall()
            cursor.execute('SELECT * FROM expenses WHERE group_id = ?', (group_id,))
            expenses = cursor.fetchall()
        return jsonify({'group': group, 'users': users, 'expenses': expenses})
    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 500

def calculate_balance(group_id):
    try:
        with sqlite3.connect('new.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT user_id FROM users WHERE group_id = ?', (group_id,))
            users = cursor.fetchall()
            user_ids = [user[0] for user in users]

            balance = {user_id: 0.0 for user_id in user_ids}
            cursor.execute('SELECT paid_by, amount FROM expenses WHERE group_id = ?', (group_id,))
            expenses = cursor.fetchall()

            for expense in expenses:
                paid_by, amount = expense
                split_amount = amount / len(users)
                for user_id in user_ids:
                    if user_id == paid_by:
                        balance[user_id] += amount - split_amount
                    else:
                        balance[user_id] -= split_amount
        return balance
    except sqlite3.Error as e:
        return {'error': str(e)}

@app.route('/get_balance/<int:group_id>', methods=['GET'])
def get_balance(group_id):
    balance = calculate_balance(group_id)
    if 'error' in balance:
        return jsonify(balance), 500
    return jsonify(balance), 200

if __name__ == '__main__':
    init_db()
    insert_sample_data()
    app.run(debug=True)