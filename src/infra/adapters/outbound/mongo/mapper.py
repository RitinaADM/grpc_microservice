from typing import Optional
from src.domain.models.document import Document
from src.infra.adapters.outbound.mongo.models import MongoDocument
from src.domain.ports.outbound.mappers.base import BaseMapper
from src.infra.adapters.outbound.mappers.utils import MapperUtils, VersionMapper

class MongoMapper(BaseMapper[Document]):
    """Маппер для преобразования между доменными объектами Document и MongoDocument."""

    def to_mongo_document(self, document: Document) -> MongoDocument:
        """Преобразует доменный Document в MongoDocument."""
        doc_dict = MapperUtils.to_json_serializable(document)
        return MongoDocument(**doc_dict)

    def to_domain_document(self, mongo_doc: MongoDocument) -> Optional[Document]:
        """Преобразует MongoDocument в доменный Document."""
        if not mongo_doc:
            return None
        # Используем dict() из beanie, но исключаем '_id' и обрабатываем поля
        doc_dict = mongo_doc.dict(exclude={'_id'})
        doc_dict['id'] = MapperUtils.deserialize_uuid(doc_dict.get('id'))
        doc_dict['created_at'] = MapperUtils.deserialize_datetime(doc_dict.get('created_at'))
        doc_dict['updated_at'] = MapperUtils.deserialize_datetime(doc_dict.get('updated_at'))
        doc_dict['status'] = MapperUtils.deserialize_status(doc_dict.get('status'))
        doc_dict['tags'] = doc_dict.get('tags', [])
        doc_dict['comments'] = doc_dict.get('comments', [])
        doc_dict['versions'] = [VersionMapper.to_domain_version(v, "mongo") for v in doc_dict.get('versions', [])]
        return Document(**doc_dict)

    def to_storage(self, document: Document) -> MongoDocument:
        """Сериализует Document в MongoDocument."""
        return self.to_mongo_document(document)

    def from_storage(self, data: Optional[MongoDocument]) -> Optional[Document]:
        """Десериализует MongoDocument в Document."""
        return self.to_domain_document(data)