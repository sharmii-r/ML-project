import tkinter as tk
from tkinter import messagebox
import sqlite3
import random
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split

# Connect to SQLite Database
conn = sqlite3.connect('food_orders_ml.db')
cursor = conn.cursor()

# Create tables if they do not exist
cursor.execute('''CREATE TABLE IF NOT EXISTS Customers (
                    customer_id INTEGER PRIMARY KEY,
                    mood TEXT,
                    recommended_food TEXT)''')
conn.commit()

# Food recommendations excluding "Fruit Bowl"
food_options = [
    'Ice Cream', 'Pasta', 'Chocolate', 'Burger', 'Fries',
    'Tacos', 'Cupcakes', 'Popcorn', 'Cookies', 'Sandwich',
    'Salad', 'Smoothie', 'Spicy Chicken Wings', 'Chili',
    'Hot Sauce', 'Sushi', 'Pizza', 'Steak', 'Quiche'
]

# Function to get food recommendations using Decision Tree
def recommend_food_decision_tree(mood):
    cursor.execute("SELECT mood, recommended_food FROM Customers")
    data = cursor.fetchall()

    # If there's not enough data, return a random food
    if len(data) < 3:  
        return random.choice(food_options)  

    df = pd.DataFrame(data, columns=['mood', 'recommended_food'])
    X = df[['mood']]
    y = df['recommended_food']

    # Convert categorical data (mood) to numerical using One-Hot Encoding
    X_encoded = pd.get_dummies(X)

    # Train-Test split for Decision Tree model
    X_train, X_test, y_train, y_test = train_test_split(X_encoded, y, test_size=0.1, random_state=42)

    # Decision Tree Classifier
    clf = DecisionTreeClassifier()
    clf.fit(X_train, y_train)

    # Prepare the input for prediction
    user_mood_df = pd.DataFrame({'mood': [mood]})
    user_mood_encoded = pd.get_dummies(user_mood_df).reindex(columns=X_encoded.columns, fill_value=0)

    # Predict food based on user mood
    recommended_food = clf.predict(user_mood_encoded)

    # Ensure the recommendation is not "Fruit Bowl"
    if recommended_food[0] == "Fruit Bowl":
        return random.choice([food for food in food_options if food != "Fruit Bowl"])
   
    return recommended_food[0]

# Function to check if the user already exists
def check_existing_user(customer_id):
    cursor.execute("SELECT mood, recommended_food FROM Customers WHERE customer_id = ?", (customer_id,))
    return cursor.fetchone()

# Function to recommend food and store user info
def recommend_food():
    customer_id = entry_user_id.get()
    mood = mood_var.get()

    if not customer_id or not mood:
        messagebox.showwarning("Input Error", "Please enter both User ID and Mood.")
        return

    existing_data = check_existing_user(customer_id)

    if existing_data:
        previous_mood, previous_food = existing_data
        messagebox.showinfo("Previous Recommendation",
                            f"Previous Mood: {previous_mood}\nRecommended Food: {previous_food}")

    # Get the new food recommendation using Decision Tree
    recommended_food = recommend_food_decision_tree(mood)

    # Store the new recommendation in the database
    cursor.execute("INSERT OR REPLACE INTO Customers (customer_id, mood, recommended_food) VALUES (?, ?, ?)",
                   (customer_id, mood, recommended_food))
    conn.commit()

    # Display the new recommendation
    messagebox.showinfo("New Recommendation",
                        f"Mood: {mood}\nRecommended Food: {recommended_food}")

# Create the main window
root = tk.Tk()
root.title("ML-Based Mood-Food Recommendation System")

# User ID Entry
tk.Label(root, text="Enter User ID:").pack(pady=5)
entry_user_id = tk.Entry(root)
entry_user_id.pack(pady=5)

# Mood Selection
mood_var = tk.StringVar(value='happy')
moods = ['happy', 'sad', 'excited', 'bored', 'relaxed', 'angry']
tk.Label(root, text="Select your mood:").pack(pady=5)
for mood in moods:
    tk.Radiobutton(root, text=mood.capitalize(), variable=mood_var, value=mood).pack(anchor='w')

# Recommend Food Button
tk.Button(root, text="Get Food Recommendation", command=recommend_food).pack(pady=20)

# Run the main loop
root.mainloop()

# Close the database connection
conn.close()