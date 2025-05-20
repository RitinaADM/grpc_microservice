from uuid import UUID
from src.domain.models.document import Document
from src.domain.ports.outbound.repository.document import DocumentRepositoryPort
from typing import List
import logging
from pymongo.errors import ConnectionFailure, OperationFailure
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from datetime import datetime

class MongoDocumentAdapter(DocumentRepositoryPort):
    """Outbound адаптер для взаимодействия с MongoDB."""
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((ConnectionFailure, OperationFailure)),
        before_sleep=lambda retry_state: logging.getLogger(__name__).warning(
            f"Retrying operation (attempt {retry_state.attempt_number}) due to {retry_state.outcome.exception()}"
        )
    )
    async def get_by_id(self, id: UUID) -> Document:
        self.logger.debug(f"Fetching document from MongoDB with ID: {id}")
        try:
            document = await Document.find_one(Document.id == id, Document.is_deleted == False)
            if document:
                return document
            self.logger.warning(f"Document not found in MongoDB: {id}")
            return None
        except ConnectionFailure as e:
            self.logger.error(f"Database connection error: {str(e)}")
            raise
        except OperationFailure as e:
            self.logger.error(f"Database operation failed: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((ConnectionFailure, OperationFailure)),
        before_sleep=lambda retry_state: logging.getLogger(__name__).warning(
            f"Retrying operation (attempt {retry_state.attempt_number}) due to {retry_state.outcome.exception()}"
        )
    )
    async def create(self, document: Document) -> Document:
        self.logger.debug(f"Creating document in MongoDB: {document.id}")
        try:
            await document.insert()
            return document
        except ConnectionFailure as e:
            self.logger.error(f"Database connection error: {str(e)}")
            raise
        except OperationFailure as e:
            self.logger.error(f"Database operation failed: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((ConnectionFailure, OperationFailure)),
        before_sleep=lambda retry_state: logging.getLogger(__name__).warning(
            f"Retrying operation (attempt {retry_state.attempt_number}) due to {retry_state.outcome.exception()}"
        )
    )
    async def update(self, id: UUID, data: dict) -> Document:
        self.logger.debug(f"Updating document in MongoDB with ID: {id}, data: {data}")
        try:
            document = await Document.find_one(Document.id == id, Document.is_deleted == False)
            if document:
                data["updated_at"] = datetime.utcnow()
                await document.set(data)
                return document
            self.logger.warning(f"Document not found in MongoDB: {id}")
            return None
        except ConnectionFailure as e:
            self.logger.error(f"Database connection error: {str(e)}")
            raise
        except OperationFailure as e:
            self.logger.error(f"Database operation failed: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((ConnectionFailure, OperationFailure)),
        before_sleep=lambda retry_state: logging.getLogger(__name__).warning(
            f"Retrying operation (attempt {retry_state.attempt_number}) due to {retry_state.outcome.exception()}"
        )
    )
    async def delete(self, id: UUID) -> bool:
        self.logger.debug(f"Soft deleting document from MongoDB with ID: {id}")
        try:
            document = await Document.find_one(Document.id == id, Document.is_deleted == False)
            if document:
                await document.set({"is_deleted": True, "updated_at": datetime.utcnow()})
                self.logger.debug(f"Successfully soft deleted document: {id}")
                return True
            self.logger.warning(f"Document not found in MongoDB: {id}")
            return False
        except ConnectionFailure as e:
            self.logger.error(f"Database connection error: {str(e)}")
            raise
        except OperationFailure as e:
            self.logger.error(f"Database operation failed: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((ConnectionFailure, OperationFailure)),
        before_sleep=lambda retry_state: logging.getLogger(__name__).warning(
            f"Retrying operation (attempt {retry_state.attempt_number}) due to {retry_state.outcome.exception()}"
        )
    )
    async def list_documents(self, skip: int, limit: int) -> List[Document]:
        self.logger.debug(f"Fetching documents from MongoDB with skip: {skip}, limit: {limit}")
        try:
            documents = await Document.find(
                Document.is_deleted == False
            ).sort("-updated_at").skip(skip).limit(limit).to_list()
            self.logger.debug(f"Fetched {len(documents)} documents from MongoDB")
            return documents
        except ConnectionFailure as e:
            self.logger.error(f"Database connection error: {str(e)}")
            raise
        except OperationFailure as e:
            self.logger.error(f"Database operation failed: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((ConnectionFailure, OperationFailure)),
        before_sleep=lambda retry_state: logging.getLogger(__name__).warning(
            f"Retrying operation (attempt {retry_state.attempt_number}) due to {retry_state.outcome.exception()}"
        )
    )
    async def restore(self, id: UUID) -> Document:
        self.logger.debug(f"Restoring document in MongoDB with ID: {id}")
        try:
            document = await Document.find_one(Document.id == id, Document.is_deleted == True)
            if document:
                await document.set({"is_deleted": False, "updated_at": datetime.utcnow()})
                self.logger.debug(f"Successfully restored document: {id}")
                return document
            self.logger.warning(f"Document not found in MongoDB: {id}")
            return None
        except ConnectionFailure as e:
            self.logger.error(f"Database connection error: {str(e)}")
            raise
        except OperationFailure as e:
            self.logger.error(f"Database operation failed: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            raise