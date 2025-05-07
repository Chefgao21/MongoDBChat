
# MongoDB Natural Language Interface

## Overview

This application bridges the gap between natural language and MongoDB query operations. Users can ask questions or give instructions in plain English, and the system will:

1. Interpret the natural language query
2. Convert it to the appropriate MongoDB operation
3. Execute the operation against your database
4. Return the results in a user-friendly format

## Features

- **Database Exploration**: Discover collections, inspect field structures, and view sample data
- **Basic Data Queries**: Filter data with simple or complex conditions and specify fields to return
- **Advanced Queries**: Sort results, implement pagination, and combine multiple query operations
- **Aggregation Operations**: Group data, filter groups, perform statistical analysis, and join collections
- **Data Modification**: Create, update, and delete documents using natural language commands
- **Field Manipulation**: Create new fields and compute values during query processing
- **Error Handling**: Validate queries, provide meaningful feedback, and recover from errors
- **Interactive Interface**: Command-line interface with persistent database connections

## Prerequisites

Before you can use this application, you need to have the following installed:

- Python 3.7 or higher
- MongoDB (either local installation or remote instance)
- OpenAI API key (for GPT-3.5 Turbo)

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/mongodb-nl-interface.git
   cd mongodb-nl-interface
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up your OpenAI API key:
   ```bash
   # On Windows
   set OPENAI_API_KEY=your_api_key_here
   
   # On macOS/Linux
   export OPENAI_API_KEY=your_api_key_here
   ```
   
   Alternatively, you'll be prompted to enter your API key when running the application.

## Configuration

By default, the application connects to a MongoDB instance running at `mongodb://localhost:27017/`. If you need to connect to a different MongoDB instance, you can modify the connection string in the code:

```python
# In the main block of mongodb_chatbot.py
connection_string = 'mongodb://your_mongodb_host:your_mongodb_port/'
```

For remote MongoDB connections with authentication, use:
```python
connection_string = 'mongodb://username:password@your_mongodb_host:your_mongodb_port/your_database'
```

## Usage

Run the application:
```bash
python mongodb_chatbot.py
```

The application will:
1. Connect to your MongoDB instance
2. Explore available databases and collections
3. Start an interactive console for natural language queries


## Code Structure

The application consists of several key components:

- **MongoDBConnector**: Handles the connection to MongoDB and executes database operations
- **NLPProcessor**: Processes natural language queries using the OpenAI API
- **QueryBuilder**: Constructs and executes MongoDB queries based on the processed NLP output
- **SchemaExplorer**: Discovers and retrieves database schema information
- **QueryClassifier**: Determines the type of query being asked
- **MongoDBChatbot**: Orchestrates the entire process and provides the user interface

## Troubleshooting

### Cannot Connect to MongoDB
- Make sure MongoDB is running on the specified host and port
- Check if authentication credentials are correct (if using authentication)
- Verify network connectivity to the MongoDB server

### OpenAI API Issues
- Verify that your API key is correct and has sufficient credits
- Check your internet connection
- Ensure that the OpenAI API is not experiencing downtime

### Query Interpretation Problems
- Try rephrasing your query to be more specific
- Make sure you're referring to existing databases and collections
- Check for typos in collection or field names

## Extending the Application

To add new functionality:

1. Extend the QueryClassifier to recognize new query types
2. Update the NLPProcessor prompt to handle the new query patterns
3. Add new methods to the QueryBuilder to handle the new operations
4. Update the MongoDBConnector if new MongoDB operations are needed


## Acknowledgements

- OpenAI for the GPT-3.5 Turbo API
- MongoDB for the powerful database system
- PyMongo for the Python-MongoDB interface
