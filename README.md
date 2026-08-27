# 🤖 AI Database Copilot

AI Database Copilot is an AI-powered **Text-to-SQL assistant** that allows users to interact with databases using natural language instead of writing SQL queries manually.

Users can ask questions such as:

> "Which products had the highest sales last month?"

The system understands the user's question, analyzes the database schema, generates an SQL query, executes it, and presents the result in an easy-to-understand format.

---

## 🚀 Key Features

* 🗣️ **Natural Language to SQL** — Ask database questions in plain English.
* 🧠 **AI-Powered SQL Generation** — Automatically generates SQL queries based on the user's question.
* 🔍 **Schema Understanding** — Uses database tables, columns, and relationships to generate relevant queries.
* ✅ **SQL Validation** — Checks generated queries before execution.
* 🔄 **Clarification Engine** — Asks follow-up questions when a user's request is ambiguous.
* 📊 **Query Results** — Displays database results in a user-friendly format.
* 💡 **SQL Explanation** — Explains the generated SQL query in simple language.
* 🛡️ **Safe Database Interaction** — Designed to reduce incorrect or unsafe query execution.

---

## 🎯 Problem Statement

Working with databases often requires knowledge of SQL.

A user may know **what information they need**, but not know how to write the SQL query required to retrieve it.

For example:

**User:**

> Show me the top 5 customers by total spending.

Instead of manually writing SQL, AI Database Copilot can understand the request and generate the appropriate query.

---

## 💡 How It Works

```text
User Question
      ↓
Natural Language Processing
      ↓
Database Schema Analysis
      ↓
SQL Generation
      ↓
SQL Validation
      ↓
Query Execution
      ↓
Results + SQL Explanation
```

---

## 🧠 Clarification Engine

One of the main features of this project is the **Clarification Engine**.

Instead of blindly generating SQL when a question is unclear, the system identifies missing information and asks the user for clarification.

### Example

**User:**

> Show me the best-selling products.

The system may ask:

> "Do you want the best-selling products based on quantity sold or total revenue?"

After the user clarifies, the system generates the appropriate SQL query.

This helps reduce incorrect results caused by ambiguous questions.

---

## 🛠️ Technologies Used

* **Python**
* **SQL**
* **PostgreSQL**
* **Pandas**
* **Streamlit**
* **LLM / Generative AI**
* **Natural Language Processing**
* **Database Metadata / Schema Analysis**

---

## 📂 Project Structure

```text
AI-Database-Copilot/
│
├── app.py
├── README.md
├── requirements.txt
├── .gitignore
│
├── database/
│   └── sample_db_setup.sql
│
├── src/
│   ├── sql_generator.py
│   ├── schema_analyzer.py
│   ├── sql_validator.py
│   └── clarification_engine.py
│
└── assets/
```

> The actual structure may vary depending on the current implementation of the project.

---

## ⚙️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/shannn9071/AI-Database-Copilot.git
```

### 2. Navigate to the project

```bash
cd AI-Database-Copilot
```

### 3. Create a virtual environment

```bash
python -m venv venv
```

### 4. Activate the virtual environment

**Windows:**

```bash
venv\Scripts\activate
```

### 5. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 🔐 Environment Variables

Create a `.env` file in the project directory and add the required configuration.

Example:

```env
DATABASE_URL=your_database_connection_string
API_KEY=your_api_key
```

**Do not upload `.env` to GitHub.**

Make sure `.env` is included in `.gitignore`.

---

## ▶️ Running the Application

If the project uses Streamlit:

```bash
streamlit run app.py
```

The application will open in your browser.

---

## 🗄️ Database

The project can be connected to a relational database such as PostgreSQL.

The database schema is analyzed to understand:

* Tables
* Columns
* Data types
* Primary keys
* Foreign keys
* Relationships

This information is provided to the AI to improve SQL generation.

---

## 💬 Example Queries

Users can ask questions such as:

```text
Which customers have placed the most orders?
```

```text
What are the top 5 products by revenue?
```

```text
How many orders were placed last month?
```

```text
Which product has the highest sales?
```

```text
Show the total revenue by category.
```

---

## 📈 Example Workflow

**Question:**

> Which products generated the highest revenue?

**AI-generated SQL:**

```sql
SELECT
    p.product_name,
    SUM(oi.quantity * oi.unit_price) AS total_revenue
FROM products p
JOIN order_items oi
    ON p.product_id = oi.product_id
GROUP BY p.product_name
ORDER BY total_revenue DESC;
```

The system executes the query and presents the resulting data to the user.

---

## 🔒 Security Considerations

The application should follow safe database practices, including:

* Read-only database access where possible
* SQL validation before execution
* Prevention of destructive SQL operations
* Environment variables for credentials
* Never exposing database passwords or API keys
* Restricting database permissions

---

## 🎓 Learning Objectives

This project demonstrates practical knowledge of:

* Generative AI
* Natural Language Processing
* Text-to-SQL
* Retrieval-Augmented Generation concepts
* Database management
* SQL
* Python
* Prompt engineering
* Schema understanding
* Query validation
* AI application development

---

## 🔮 Future Improvements

* Support for multiple database types
* Advanced RAG-based schema retrieval
* Automatic query optimization
* Query history
* Data visualization recommendations
* Role-based database access
* Voice-based database queries
* Multi-turn conversations
* Automatic chart generation
* Improved SQL error correction
* Database performance monitoring

---

## 👨‍💻 Author

**Shantharaj k **
---

## 📄 License

This project is intended for educational and portfolio purposes.
