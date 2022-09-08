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
                decoded: dict = jwt.decode(token, verify=False)

                user_id = decoded.get("sub")
                is_staff = decoded.get("is_staff")
                is_admin = decoded.get("is_admin")

                user = OriginUser(
                    user_id=user_id,
                    is_staff=is_staff,
                    is_admin=is_admin,
                )

            except Exception as e:
                print("Error in origin user", e)
                user = None

        request.origin_user = user

        return None
