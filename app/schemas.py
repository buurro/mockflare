from pydantic import BaseModel


class CloudflareError(BaseModel):
    code: int
    message: str


class ResultInfo(BaseModel):
    page: int = 1
    per_page: int = 20
    total_pages: int = 1
    count: int = 0
    total_count: int = 0


class CloudflareResponse[T](BaseModel):
    success: bool = True
    errors: list[CloudflareError] = []
    messages: list[str] = []
    result: T | None = None


class CloudflareListResponse[T](BaseModel):
    success: bool = True
    errors: list[CloudflareError] = []
    messages: list[str] = []
    result: list[T] = []
    result_info: ResultInfo | None = None


class DeleteResponse(BaseModel):
    id: str


def make_response[T](result: T) -> CloudflareResponse[T]:
    return CloudflareResponse(success=True, result=result)


def make_list_response[T](
    results: list[T],
    page: int = 1,
    per_page: int = 20,
    total_count: int | None = None,
) -> CloudflareListResponse[T]:
    count = len(results)
    total = total_count if total_count is not None else count
    total_pages = (total + per_page - 1) // per_page if per_page > 0 else 1

    return CloudflareListResponse(
        success=True,
        result=results,
        result_info=ResultInfo(
            page=page,
            per_page=per_page,
            total_pages=total_pages,
            count=count,
            total_count=total,
        ),
    )
