from fastapi import HTTPException, status


class NotFoundError(HTTPException):
    def __init__(self, resource: str, id: str) -> None:
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=f"{resource} '{id}' not found.")


class ConflictError(HTTPException):
    def __init__(self, detail: str) -> None:
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class ProcessingError(HTTPException):
    def __init__(self, detail: str) -> None:
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)
