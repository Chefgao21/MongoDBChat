import json
import re
import sys
from typing import Dict, List, Any
from openai import OpenAI
import pymongo
from bson import ObjectId

class MongoDBConnector:
    
    def __init__(self, connection_string: str = 'mongodb://localhost:27017/'):
        try:
            self.client = pymongo.MongoClient(connection_string)
            self.client.admin.command('ping')
            print("Connected to MongoDB successfully!")
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")
            raise
        
    def get_databases(self) -> List[str]:
        return [db for db in self.client.list_database_names() 
                if db not in ['admin', 'local', 'config']]
    
    def get_collections(self, database_name: str) -> List[str]:
        db = self.client[database_name]
        return db.list_collection_names()
    
    def get_sample_data(self, database_name: str, collection_name: str, limit: int = 5) -> List[Dict]:
        db = self.client[database_name]
        collection = db[collection_name]
        return list(collection.find().limit(limit))
    
    def get_collection_schema(self, database_name: str, collection_name: str) -> Dict[str, str]:
        db = self.client[database_name]
        collection = db[collection_name]
        sample = collection.find_one()
        
        if not sample:
            return {}
        
        schema = {}
        for key, value in sample.items():
            schema[key] = type(value).__name__
        
        return schema
    
    def execute_find(self, database_name: str, collection_name: str, 
                    query_filter: Dict = None, projection: Dict = None,
                    sort: List = None, limit: int = None, skip: int = None) -> List[Dict]:
        db = self.client[database_name]
        collection = db[collection_name]
        
        cursor = collection.find(filter=query_filter or {}, projection=projection)
        
        if sort:
            cursor = cursor.sort(sort)
        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)
            
        return list(cursor)
    
    def execute_aggregate(self, database_name: str, collection_name: str, 
                         pipeline: List[Dict]) -> List[Dict]:
        db = self.client[database_name]
        collection = db[collection_name]
        return list(collection.aggregate(pipeline))
    
    def execute_insert_one(self, database_name: str, collection_name: str, 
                          document: Dict) -> Dict:
        db = self.client[database_name]
        collection = db[collection_name]
        result = collection.insert_one(document)
        return {"acknowledged": result.acknowledged, "inserted_id": result.inserted_id}
    
    def execute_insert_many(self, database_name: str, collection_name: str, 
                           documents: List[Dict]) -> Dict:
        db = self.client[database_name]
        collection = db[collection_name]
        result = collection.insert_many(documents)
        return {"acknowledged": result.acknowledged, "inserted_ids": result.inserted_ids}
    
    def execute_update_one(self, database_name: str, collection_name: str, 
                          filter_query: Dict, update_query: Dict, upsert: bool = False) -> Dict:
        db = self.client[database_name]
        collection = db[collection_name]
        result = collection.update_one(filter_query, update_query, upsert=upsert)
        return {
            "acknowledged": result.acknowledged,
            "matched_count": result.matched_count,
            "modified_count": result.modified_count,
            "upserted_id": result.upserted_id
        }
    
    def execute_update_many(self, database_name: str, collection_name: str, 
                           filter_query: Dict, update_query: Dict, upsert: bool = False) -> Dict:
        db = self.client[database_name]
        collection = db[collection_name]
        result = collection.update_many(filter_query, update_query, upsert=upsert)
        return {
            "acknowledged": result.acknowledged,
            "matched_count": result.matched_count,
            "modified_count": result.modified_count,
            "upserted_id": result.upserted_id
        }
    
    def execute_delete_one(self, database_name: str, collection_name: str, 
                          filter_query: Dict) -> Dict:
        db = self.client[database_name]
        collection = db[collection_name]
        result = collection.delete_one(filter_query)
        return {"acknowledged": result.acknowledged, "deleted_count": result.deleted_count}
    
    def execute_delete_many(self, database_name: str, collection_name: str, 
                           filter_query: Dict) -> Dict:
        db = self.client[database_name]
        collection = db[collection_name]
        result = collection.delete_many(filter_query)
        return {"acknowledged": result.acknowledged, "deleted_count": result.deleted_count}
    
    def count_documents(self, database_name: str, collection_name: str, 
                       filter_query: Dict = None) -> int:
        db = self.client[database_name]
        collection = db[collection_name]
        return collection.count_documents(filter_query or {})


class NLPProcessor:
    
    def __init__(self, api_key):
        print("Initializing OpenAI GPT-3.5 Turbo...")
        self.client = OpenAI(api_key=api_key)
        print("OpenAI client initialized successfully!")
        
    def process_query(self, query: str, schema_info: Dict) -> Dict:
        prompt = self._build_prompt(query, schema_info)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a MongoDB query assistant that converts natural language to MongoDB queries."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  
                max_tokens=1024
            )
            
            response_text = response.choices[0].message.content
            
            print("\nRaw GPT-3.5 response:")
            print("-" * 80)
            print(response_text)
            print("-" * 80)
            
            parsed_query = self._parse_response(response_text)
            return parsed_query
            
        except Exception as e:
            print(f"Error calling OpenAI API: {str(e)}")
            return {"error": f"OpenAI API error: {str(e)}"}
        
    def _build_prompt(self, query: str, schema_info: Dict) -> str:
        db_structure = "Available databases and collections:\n"
        for db_name, db_info in schema_info["databases"].items():
            collections = list(db_info["collections"].keys())
            db_structure += f"- Database: {db_name}, Collections: {', '.join(collections)}\n"
        
        prompt = f"""
        You are a MongoDB query assistant. Convert the following natural language query to a structured MongoDB operation.
        
        {db_structure}
        
        User query: {query}
        
        IMPORTANT: Make sure to select the correct database and collection names from the available options listed above.
        
        Output ONLY a valid JSON object with the following structure with NO explanations or additional text:
        {{
        "database": "[exact database name from the list above]",
        "collection": "[exact collection name from the list above]",
        "operation": "[find/aggregate/insert_one/update_one/delete_one/etc]",
        "parameters": {{
            "filter": {{
                // filter conditions go here
            }},
            // other operation-specific parameters
        }}
        }}
        
        For find operations, ALWAYS put filter conditions inside a "filter" object within parameters.
        """
        return prompt
            
    def _parse_response(self, response: str) -> Dict:
        try:
            cleaned_response = response.replace("```json", "").replace("```", "").strip()
            query_info = json.loads(cleaned_response)
            return query_info
        except json.JSONDecodeError:
            try:
                json_pattern = r'\{.*\}'
                match = re.search(json_pattern, response, re.DOTALL)
                if match:
                    query_info = json.loads(match.group(0))
                    return query_info
            except (json.JSONDecodeError, AttributeError):
                pass
            
        return {"error": "No valid JSON found in response"}


class QueryBuilder:
    
    def __init__(self, db_connector: MongoDBConnector):
        self.db_connector = db_connector
        
    def build_and_execute(self, parsed_query: Dict) -> Dict:
        try:
            if "error" in parsed_query:
                return {"error": parsed_query["error"]}
            
            database = parsed_query.get("database")
            collection = parsed_query.get("collection")
            operation = parsed_query.get("operation")
            parameters = parsed_query.get("parameters", {})
            
            if not all([database, collection, operation]):
                return {"error": "Missing required query components"}
            
            if operation == "find":
                return self._handle_find(database, collection, parameters)
            elif operation == "aggregate":
                return self._handle_aggregate(database, collection, parameters)
            elif operation == "insert_one":
                return self._handle_insert_one(database, collection, parameters)
            elif operation == "insert_many":
                return self._handle_insert_many(database, collection, parameters)
            elif operation == "update_one":
                return self._handle_update_one(database, collection, parameters)
            elif operation == "update_many":
                return self._handle_update_many(database, collection, parameters)
            elif operation == "delete_one":
                return self._handle_delete_one(database, collection, parameters)
            elif operation == "delete_many":
                return self._handle_delete_many(database, collection, parameters)
            elif operation == "count":
                return self._handle_count(database, collection, parameters)
            else:
                return {"error": f"Unsupported operation: {operation}"}
            
        except Exception as e:
            return {"error": f"Error executing query: {str(e)}"}
    
    def _serialize_result(self, result: Dict) -> Dict:
        serialized = {}
        for key, value in result.items():
            if hasattr(value, '__str__') and "ObjectId" in str(type(value)):
                serialized[key] = str(value)
            elif isinstance(value, list) and all(hasattr(item, '__str__') and "ObjectId" in str(type(item)) for item in value):
                serialized[key] = [str(item) for item in value]
            else:
                serialized[key] = value
        return serialized
    
    def _handle_find(self, database: str, collection: str, parameters: Dict) -> Dict:
        filter_query = parameters.get("filter", {})
        projection = parameters.get("projection")
        sort = parameters.get("sort")
        limit = parameters.get("limit")
        skip = parameters.get("skip")
        
        result = self.db_connector.execute_find(
            database, collection, filter_query, projection, sort, limit, skip
        )
        
        return {"result": self._serialize_for_json(result), "count": len(result)}
    
    def _handle_aggregate(self, database: str, collection: str, parameters: Dict) -> Dict:
        pipeline = parameters.get("pipeline", [])
        
        result = self.db_connector.execute_aggregate(database, collection, pipeline)
        
        return {"result": self._serialize_for_json(result), "count": len(result)}
    
    def _handle_insert_one(self, database: str, collection: str, parameters: Dict) -> Dict:
        document = parameters.get("document", {})
        
        result = self.db_connector.execute_insert_one(database, collection, document)
        
        return self._serialize_result(result)
    
    def _handle_insert_many(self, database: str, collection: str, parameters: Dict) -> Dict:
        documents = parameters.get("documents", [])
        
        result = self.db_connector.execute_insert_many(database, collection, documents)
        
        return self._serialize_result(result)
    
    def _handle_update_one(self, database: str, collection: str, parameters: Dict) -> Dict:
        filter_query = parameters.get("filter", {})
        update = parameters.get("update", {})
        upsert = parameters.get("upsert", False)
        
        result = self.db_connector.execute_update_one(
            database, collection, filter_query, update, upsert
        )
        
        return self._serialize_result(result)
    
    def _handle_update_many(self, database: str, collection: str, parameters: Dict) -> Dict:
        filter_query = parameters.get("filter", {})
        update = parameters.get("update", {})
        upsert = parameters.get("upsert", False)
        
        result = self.db_connector.execute_update_many(
            database, collection, filter_query, update, upsert
        )
        
        return self._serialize_result(result)
    
    def _handle_delete_one(self, database: str, collection: str, parameters: Dict) -> Dict:
        filter_query = parameters.get("filter", {})
        
        result = self.db_connector.execute_delete_one(database, collection, filter_query)
        
        return self._serialize_result(result)
    
    def _handle_delete_many(self, database: str, collection: str, parameters: Dict) -> Dict:
        filter_query = parameters.get("filter", {})
        
        result = self.db_connector.execute_delete_many(database, collection, filter_query)
        
        return self._serialize_result(result)
    
    def _handle_count(self, database: str, collection: str, parameters: Dict) -> Dict:
        filter_query = parameters.get("filter", {})
        
        count = self.db_connector.count_documents(database, collection, filter_query)
        
        return {"count": count}
    
    def _serialize_for_json(self, data: Any) -> Any:
        if isinstance(data, list):
            return [self._serialize_for_json(item) for item in data]
        elif isinstance(data, dict):
            result = {}
            for key, value in data.items():
                if key == '_id' and hasattr(value, '__str__'):
                    result[key] = str(value)
                else:
                    result[key] = self._serialize_for_json(value)
            return result
        else:
            return data


class SchemaExplorer:
    
    def __init__(self, db_connector: MongoDBConnector):
        self.db_connector = db_connector
        
    def get_all_schema_info(self) -> Dict:
        schema_info = {"databases": {}}
        
        databases = self.db_connector.get_databases()
        
        for db_name in databases:
            schema_info["databases"][db_name] = {"collections": {}}
            
            collections = self.db_connector.get_collections(db_name)
            
            for coll_name in collections:
                coll_schema = self.db_connector.get_collection_schema(db_name, coll_name)
                sample_data = self.db_connector.get_sample_data(db_name, coll_name, limit=1)
                
                schema_info["databases"][db_name]["collections"][coll_name] = {
                    "schema": coll_schema,
                    "sample": self._serialize_for_json(sample_data[0]) if sample_data else None
                }
        
        return schema_info
    
    def _serialize_for_json(self, data: Any) -> Any:
        if isinstance(data, list):
            return [self._serialize_for_json(item) for item in data]
        elif isinstance(data, dict):
            result = {}
            for key, value in data.items():
                if key == '_id' and hasattr(value, '__str__'):
                    result[key] = str(value)
                else:
                    result[key] = self._serialize_for_json(value)
            return result
        else:
            return data


class QueryClassifier:
    def classify_query(self, query: str) -> str:
        query = query.lower()
        
        schema_keywords = [
            "what collections", "what tables", "show collections", "show tables",
            "what fields", "what columns", "schema", "structure", "sample data"
        ]
        
        for keyword in schema_keywords:
            if keyword in query:
                return "schema_exploration"
        
        if any(kw in query for kw in ["add", "insert", "create", "put"]):
            return "data_modification_insert"
        
        if any(kw in query for kw in ["update", "change", "modify", "set"]):
            return "data_modification_update"
        
        if any(kw in query for kw in ["delete", "remove", "drop"]):
            return "data_modification_delete"
        
        return "query"

class MongoJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return super().default(obj)
    
class MongoDBChatbot:
    
    def __init__(self, connection_string: str = 'mongodb://localhost:27017/', openai_api_key: str = None):
        self.db_connector = MongoDBConnector(connection_string)
        
        self.schema_explorer = SchemaExplorer(self.db_connector)
        self.query_classifier = QueryClassifier()
        
        if openai_api_key:
            try:
                self.nlp_processor = NLPProcessor(openai_api_key)
                self.query_builder = QueryBuilder(self.db_connector)
            except Exception as e:
                print(f"Error initializing NLP model: {e}")
                print("Running in limited functionality mode without NLP processing.")
                self.nlp_processor = None
                self.query_builder = None
        else:
            print("No OpenAI API key provided. Running in limited functionality mode.")
            self.nlp_processor = None
            self.query_builder = None
            
        self.schema_info = self.schema_explorer.get_all_schema_info()
        
    def process_user_query(self, query: str) -> Dict:
        query_type = self.query_classifier.classify_query(query)
        
        if query_type == "schema_exploration":
            return self._handle_schema_exploration(query)
        
        if not self.nlp_processor:
            return {"status": "error", "message": "NLP processor not available"}
        
        try:
            print("\nSending query to NLP model...")
            parsed_query = self.nlp_processor.process_query(query, self.schema_info)
            
            if "error" in parsed_query:
                print(f"\nNLP processing error: {parsed_query['error']}")
                return {"status": "error", "message": parsed_query["error"]}
            
            print("\nExecuting MongoDB query...")
            result = self.query_builder.build_and_execute(parsed_query)
            
            if "error" in result:
                return {"status": "error", "message": result["error"]}
            else:
                return {"status": "success", "data": result, "query": parsed_query}
        except Exception as e:
            print(f"\nException during query processing: {str(e)}")
            return {"status": "error", "message": f"Error processing query: {str(e)}"}
    
    def _handle_schema_exploration(self, query: str) -> Dict:
        query_lower = query.lower()
        
        db_name = None
        coll_name = None
        
        for db in self.schema_info["databases"]:
            if db.lower() in query_lower:
                db_name = db
                break
        
        if db_name:
            for coll in self.schema_info["databases"][db_name]["collections"]:
                if coll.lower() in query_lower:
                    coll_name = coll
                    break
        
        if db_name and coll_name:
            collection_info = self.schema_info["databases"][db_name]["collections"][coll_name]
            
            if "sample" in query_lower or "example" in query_lower:
                samples = self.db_connector.get_sample_data(db_name, coll_name, limit=5)
                collection_info["samples"] = [self.query_builder._serialize_for_json(s) for s in samples]
            
            return {
                "status": "success",
                "data": {
                    "database": db_name,
                    "collection": coll_name,
                    "info": collection_info
                }
            }
        elif db_name:
            return {
                "status": "success",
                "data": {
                    "database": db_name,
                    "collections": list(self.schema_info["databases"][db_name]["collections"].keys())
                }
            }
        else:
            db_list = {}
            for db in self.schema_info["databases"]:
                db_list[db] = list(self.schema_info["databases"][db]["collections"].keys())
            
            return {
                "status": "success",
                "data": {
                    "databases": db_list
                }
            }
        
    def _ensure_serializable(self, obj):
        if isinstance(obj, dict):
            return {k: self._ensure_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._ensure_serializable(item) for item in obj]
        elif hasattr(obj, '__str__') and "ObjectId" in str(type(obj)):
            return str(obj)
        else:
            return obj
    
    def run_interactive(self):
        print("\nMongoDB Natural Language Interface")
        print("=================================")
        print("Available databases:")
        
        for db_name in self.schema_info["databases"]:
            collections = list(self.schema_info["databases"][db_name]["collections"].keys())
            print(f"- {db_name}: {', '.join(collections)}")
        
        while True:
            try:
                query = input("\nEnter your query: ")
                
                if query.lower() in ['exit', 'quit']:
                    print("\nGoodbye!")
                    break
                
                print("\nProcessing query...")
                result = self.process_user_query(query)
                
                if result["status"] == "error":
                    print(f"\nError: {result['message']}")
                else:
                    print("\nResult:")
                    print(json.dumps(result["data"], indent=2, cls=MongoJSONEncoder))
                    
                    if "query" in result:
                        print("\nInterpreted as:")
                        print(json.dumps(result["query"], indent=2, cls=MongoJSONEncoder))
            
            except KeyboardInterrupt:
                print("\n\nExiting...")
                break
            except Exception as e:
                print(f"\nAn error occurred: {str(e)}")


if __name__ == "__main__":
    try:
        import os
        openai_api_key = os.environ.get("OPENAI_API_KEY")
        
        if not openai_api_key:
            openai_api_key = input("Enter your OpenAI API key (or set OPENAI_API_KEY environment variable): ")
        
        print("Initializing MongoDB Natural Language Interface...")
        
        connection_string = 'mongodb://localhost:27017/'
        chatbot = MongoDBChatbot(connection_string, openai_api_key)
        
        chatbot.run_interactive()
    except Exception as e:
        print(f"Error initializing the application: {str(e)}")
        sys.exit(1)