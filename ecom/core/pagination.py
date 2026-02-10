# core/pagination.py
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardResultsPagination(PageNumberPagination):
    page_size = 10
    # page_size_query_param = "page_size"
    # max_page_size = 100

    def get_paginated_response(self, data):
        view = self.request.parser_context.get("view")

        message = "Records retrieved successfully."

        if view:
            action = getattr(view, "action", None)
            action_messages = getattr(view, "action_messages", {})

            if action and action in action_messages:
                message = action_messages[action]
            else:
                message = getattr(view, "list_message", message)

        return Response(
            {
                "status": "success",
                "code": "FETCH_SUCCESSFUL",
                "message": message,
                "meta": {
                    "count": self.page.paginator.count,
                    "next": self.get_next_link(),
                    "previous": self.get_previous_link(),
                    "page": self.page.number,
                    "page_size": self.get_page_size(self.request),
                },
                "data": data,
            }
        )
