from rest_framework.pagination import PageNumberPagination


class CustomLimitPagination(PageNumberPagination):
    """Класс пагинатор.
    Атрибуты:
        - `page_size_query_param`- для вывода запрошенного количества страниц.
    """

    page_size_query_param = "limit"
