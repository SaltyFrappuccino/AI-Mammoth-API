from langchain_chroma import Chroma
from langchain_gigachat.embeddings.gigachat import GigaChatEmbeddings
from chromadb.config import Settings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
import logging
import traceback

logger = logging.getLogger("semantic_db")

class SemanticDB:
    def __init__(self, embeddings, documents=None):
        logger.info("Initializing SemanticDB")
        self.embeddings = embeddings
        
        try:
            self.db = Chroma(
                embedding_function=embeddings,
                client_settings=Settings(anonymized_telemetry=False))
            
            # Check what type of data we received
            if documents is not None:
                logger.info(f"Documents provided, type: {type(documents).__name__}")
                
                # If documents is a dictionary (service_name: description format)
                if isinstance(documents, dict):
                    if "documents" in documents and isinstance(documents["documents"], list):
                        # Old format with "documents" key containing a list
                        logger.info(f"Old format detected with 'documents' key containing {len(documents['documents'])} items")
                        self.add_documents(documents["documents"])
                    else:
                        # New format: dictionary mapping service names to descriptions
                        logger.info(f"New format detected: dictionary with {len(documents)} service descriptions")
                        self.add_service_descriptions(documents)
                # If documents is a list of text strings
                elif isinstance(documents, list):
                    logger.info(f"List format detected with {len(documents)} items")
                    self.add_documents(documents)
                else:
                    logger.warning(f"Unsupported document format: {type(documents).__name__}")
        except Exception as e:
            logger.error(f"Error initializing SemanticDB: {str(e)}")
            logger.error(traceback.format_exc())
            raise RuntimeError(f"Failed to initialize SemanticDB: {str(e)}")
    
    def add_documents(self, documents):
        """Add a list of text documents to the database"""
        logger.info(f"Adding {len(documents)} documents to the database")
        try:
            # Check if documents are all strings
            if not all(isinstance(doc, str) for doc in documents):
                # Try to convert non-string items to strings
                documents = [str(doc) for doc in documents]
                logger.warning("Converted non-string documents to strings")
                
            self.db.add_texts(documents)
            logger.info("Successfully added documents")
        except Exception as e:
            logger.error(f"Error adding documents: {str(e)}")
            logger.error(traceback.format_exc())
            raise RuntimeError(f"Failed to add documents to database: {str(e)}")
    
    def add_service_descriptions(self, service_descriptions):
        """
        Process a dictionary of service descriptions in the format:
        { "serviceName": "serviceDescription", ... }
        """
        logger.info(f"Adding service descriptions for {len(service_descriptions)} services")
        try:
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
            )
            
            documents = []
            for service_name, description in service_descriptions.items():
                # Skip empty or None descriptions
                if not description:
                    logger.warning(f"Skipping empty description for service: {service_name}")
                    continue
                    
                # Convert non-string descriptions to strings
                if not isinstance(description, str):
                    description = str(description)
                    logger.warning(f"Converted non-string description to string for service: {service_name}")
                
                # Create a document with metadata containing the service name
                doc = Document(
                    page_content=description,
                    metadata={"service_name": service_name}
                )
                documents.append(doc)
            
            if not documents:
                logger.warning("No valid documents to add")
                return
                
            # Split documents into chunks for better retrieval
            split_docs = text_splitter.split_documents(documents)
            logger.info(f"Split {len(documents)} documents into {len(split_docs)} chunks")
            
            # Add the documents to the database
            self.db.add_documents(split_docs)
            logger.info("Successfully added service descriptions")
        except Exception as e:
            logger.error(f"Error adding service descriptions: {str(e)}")
            logger.error(traceback.format_exc())
            raise RuntimeError(f"Failed to add service descriptions to database: {str(e)}")
    
    def search(self, query: str, k: int = 3) -> list:
        logger.info(f"Searching for: '{query}' with k={k}")
        try:
            docs = self.db.similarity_search(query, k=k)
            logger.info(f"Found {len(docs)} documents")
            return [doc.page_content for doc in docs]
        except Exception as e:
            logger.error(f"Error during search: {str(e)}")
            logger.error(traceback.format_exc())
            return [f"Error during search: {str(e)}"]
    
    def query_service(self, service_name: str) -> str:
        """Get information about a specific service by name"""
        logger.info(f"Querying service: {service_name}")
        try:
            docs = self.db.similarity_search(
                f"Information about service {service_name}",
                k=1
            )
            if docs:
                logger.info(f"Found information for service: {service_name}")
                return docs[0].page_content
            logger.info(f"No information found for service: {service_name}")
            return f"No information found for service {service_name}"
        except Exception as e:
            logger.error(f"Error querying service {service_name}: {str(e)}")
            logger.error(traceback.format_exc())
            return f"Error retrieving information for service {service_name}: {str(e)}"