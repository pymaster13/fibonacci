from rest_framework.pagination import LimitOffsetPagination


class SmallResultsSetPagination(LimitOffsetPagination):
    page_size = 1
    page_size_query_param = 'page_size'
    max_page_size = 1
