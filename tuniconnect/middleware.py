from django.contrib.messages import get_messages

class ClearMessagesMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # изчистваме messages след response
        storage = get_messages(request)
        for _ in storage:
            pass

        return response