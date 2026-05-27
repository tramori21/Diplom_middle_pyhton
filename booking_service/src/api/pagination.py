from fastapi import Query


class Pagination:
    def __init__(
        self,
        page_number: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
    ) -> None:
        self.page_number = page_number
        self.page_size = page_size

    @property
    def offset(self) -> int:
        return (self.page_number - 1) * self.page_size