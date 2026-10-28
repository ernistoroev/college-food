from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    """
    Lists come in pages: {count, next, previous, results}.
    ?page=2 — the next page; ?page_size=100 — a bigger page (up to 100), e.g. the whole menu at once.
    """

    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
