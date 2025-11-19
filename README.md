# 📘 Social Network Graph Application

*A Python + Neo4j Graph Database Project*

## 📌 Overview

This project implements a simplified social networking system backed by a **Neo4j graph database**.
The system allows users to register, log in, follow others, explore connections, and run graph-based queries.
A **Streamlit-based UI** provides both **Admin View** (use-case testing) and **User View** (Instagram-style profile).

This project fulfills the **CS157C – Final Project** requirements:

* Graph modeling using Neo4j
* Real-world-scale dataset (1000 users, 5000+ FOLLOWS relationships)
* Implementation of **11 use cases** (User Mgmt + Social Features + Search)
* Report + Code + Screenshots

---

## 🧱 Technologies Used

### **Backend / Database**

* **Neo4j 5.x**
* Cypher Query Language
* Neo4j Python Driver

### **Frontend**

* **Streamlit**
* PyVis (graph visualization)
* Pandas (tabular data output)

### **Dataset**

* 5000 synthetic users
* 5000–20,000 FOLLOWS edges

Refer `db_setup/generate_users.py` and `db_setup/generate_graph.py` for implementation details of the synthetic dataset.

---
## Installation

### Clone Repository
```
git clone https://github.com/Aditya-Dawadikar/CS157C-Final-Project.git
```

Navigate to the project folder
```
cd CS157C-Final-Project
```

Create a Python Virtual Environment (Windows System)
```
python -m venv venv
.\venv\Scripts\activate
```

Install dependencies
```
pip install -r requirements.txt
```
---

## Create Dataset

Navigate to `db_setup` folder
```
cd db_setup
```

### Create Users
```
python generate_users.py
```
This file will generate 5000 unique users.

### Create Relationships
```
python generate_graph.py
```
This file will add A-[FOLLOWS]->B type of relationships

### Ingest Data to Neo4j

For this step, ensure that Neo4j client is installed on your device. Create an Instance named `SocialNetwork` and a database named `socialnetworkdb`.

Let the user for the DB be `neo4j` and password be `neo4juser`. If you use a different password, please update it in the scripts, but do not push those lines of code to the github repo.

Your setup must following this:
```
NEO4J_URI = "neo4j://127.0.0.1:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "neo4juser"
DB_NAME = "socialnetworkdb"
```

Note: NEO4J_URI may change depending on your installation.

Once the database is up and running, we will ingest our newly created users and graph into the db.

```
python ingest_graph.py
```

This script will read the `users.csv` and `follows.csv`, and insert the data to database. In the case when data already exists in the database, retriggering this script will delete the old data from database, and ingest a new copy. Always make sure the `users.csv` and `follows.csv` exists in the same folder as `ingest_graph.py`.

---

## 📊 Property Graph Schema

### **Node: `User`**

| Property       | Type   | Description                    |
| -------------- | ------ | ------------------------------ |
| `userId`       | STRING | Zero-padded ID (`0001…5000`)   |
| `username`     | STRING | Generated username             |
| `email`        | STRING | Unique user email              |
| `name`         | STRING | Full display name              |
| `bio`          | STRING | Short profile biography        |
| `passwordHash` | STRING | bcrypt hashed password         |

### **Relationship: `FOLLOWS`**

User A → User B
Represents *A follows B* (directed edge).

---

## 📦 Dataset Generation

### 1. **User Generator (`generate_users.py`)**

* Creates **5000 unique users**
* Usernames: *Adjective + Noun + Number*
* Emails: `user_XXXX@example.com`
* Every user gets the same password `password` (bcrypt hashed)
* Logs progress every 100 users

### 2. **Graph Generator (`generate_graph.py`)**

Creates realistic social graph behavior:

* Randomized follows (3–50)
* Cluster-based follows
* Ghost accounts (0 followers)
* Influencers (up to 500+ followers)
* Repeatable results (using `random.seed`)

### 3. **Ingestion (`ingest_graph.py`)**

* Creates constraints
* Deletes existing graph
* Loads all users
* Loads all FOLLOWS relationships

---

## 🗑 Database Cleanup

Use:

```bash
python cleanup_db.py
```

Drops all nodes and edges so you can start fresh.

---

## 🖥 Running the UI

### 1. Install dependencies

```
pip install -r requirements.txt
```

### 2. Start Streamlit

```
streamlit run app/streamlit_app.py
```

### 3. Make sure Neo4j is running

Update DB config in:

```
app/db/config.py
```

---

## 🧭 Application Views

### 🔐 **User View**

After login:

* Profile summary
* Followers count
* Following count
* List of followers
* List of accounts you follow

Password:

```
password
```

(Stored using bcrypt)

---

### 🛠 **Admin View**

Implements all **11 Use Cases** with:

* Editable Cypher queries
* Run + Reset buttons
* Table and graph visualization
* Console logs for executed Cypher

---

## Implemented Use Cases

### **User Management**

1. UC-1: User Registration
2. UC-2: Login
3. UC-3: View Profile
4. UC-4: Edit Profile

### **Social Graph**

5. UC-5: Follow User
6. UC-6: Unfollow User
7. UC-7: View Friends/Connections
8. UC-8: Mutual Connections
9. UC-9: Friend Recommendations

### **Search & Explore**

10. UC-10: Search Users
11. UC-11: Explore Popular Users

Each UC panel includes:

* Cypher query (editable)
* Query output + graph visualization
* Matching screenshot (for report)

---

## 👥 Team Info

> Replace with actual team members before submission.

```
Team Members:
- Aditya Dawadikar – Dataset, Schema, Search & Explore
- Timothy – User Management
- Jakob – Social Graph Features
```
