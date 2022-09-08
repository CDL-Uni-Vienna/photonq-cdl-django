import jwt


class OriginMidddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        self.process_request(request)

        response = self.get_response(request)
        return response

    def process_request(self, request):

        class OriginUser:
            def __init__(self, user_id=None, is_staff=False, is_admin=False):
                self.id = user_id
                self.is_staff = is_staff
                self.is_admin = is_admin

        user = None

        # Check if the request has a token
        if "HTTP_AUTHORIZATION" in request.META:

            token = request.META["HTTP_AUTHORIZATION"].split(" ")[1]
            try:
                decoded = jwt.decode(token, verify=False)

                user = OriginUser(
                    decoded["sub"],
                    is_admin=decoded["is_admin"],
                    is_staff=decoded["is_staff"]
                )

            except:
                user = None

        request.origin_user = user

        return None
