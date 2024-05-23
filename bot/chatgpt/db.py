import os

class LocalDatabase:
    def __init__(self, filename, delimiter=','):
        self.filename = filename
        self.delimiter = delimiter
        self.data = {}

        if os.path.exists(filename):
            self.load_data()
        else:
            with open(filename, 'w') as f:
                pass

    def load_data(self):
        with open(self.filename, 'r') as f:
            for line in f:
                username, points = line.strip().split(self.delimiter)
                self.data[username] = int(points)

    def save_data(self):
        with open(self.filename, 'w') as f:
            for username, points in self.data.items():
                f.write(f"{username}{self.delimiter}{points}\n")

    def add_user(self, username, points=0):
        if username not in self.data:
            self.data[username] = points
            self.save_data()
            return True
        else:
            print("User already exists.")
            return False

    def add_points(self, username, points):
        if username in self.data:
            self.data[username] += points
            self.save_data()
        else:
            print("User does not exist.")

    def deduct_points(self, username, points):
        if username in self.data:
            if self.data[username] >= points:
                self.data[username] -= points
                self.save_data()
            else:
                print("Insufficient points.")
        else:
            print("User does not exist.")

    def get_points(self, username):
        if username in self.data:
            return self.data[username]
        else:
            print("User does not exist.")
            return None

# Example usage:
db = LocalDatabase("user.txt")

# Add new user
db.add_user("user1", 100)

# Add points
db.add_points("user1", 50)

# Deduct points
db.deduct_points("user1", 30)

# Get points
print("User1 points:", db.get_points("user1"))
