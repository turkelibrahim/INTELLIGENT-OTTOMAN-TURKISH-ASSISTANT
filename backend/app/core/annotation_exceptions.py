from fastapi import HTTPException, status

class AnnotationException(HTTPException):
    def __init__(self, status_code: int, error_code: str, message: str, details: list = None, entity_type: str = None, entity_id: int = None):
        super().__init__(
            status_code=status_code,
            detail={
                "error": {
                    "code": error_code,
                    "message": message,
                    "details": details or [],
                    "entity_type": entity_type,
                    "entity_id": entity_id
                }
            }
        )

def not_found(entity_type: str, entity_id: int):
    return AnnotationException(404, "ANNOTATION_NOT_FOUND", f"{entity_type} {entity_id} not found", entity_type=entity_type, entity_id=entity_id)

def locked_entity(entity_type: str, entity_id: int):
    return AnnotationException(409, "LOCKED_ENTITY", f"{entity_type} {entity_id} is locked", entity_type=entity_type, entity_id=entity_id)
