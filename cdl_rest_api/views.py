from django.contrib.auth import login
from rest_framework import permissions
from rest_framework.serializers import Serializer

from rest_framework.views import APIView
from rest_framework.response import Response  # Standard Response object
from rest_framework import status

from rest_framework import generics


from rest_framework.authtoken.serializers import AuthTokenSerializer

# from rest_framework.settings import api_settings
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny


from knox.views import LoginView as KnoxLoginView

from cdl_rest_api import serializers
from cdl_rest_api import models
from cdl_rest_api.permissions import UpdateOwnProfile


# instead of check for primarykey we create multiple endpoints
class ExperimentDetailView(APIView):
    """ """

    permission_classes = (IsAuthenticated,)
    # serializers_class = serializers.ExperimentSerializer

    def get(self, request, experiment_id):
        """ """
        experiment = None
        experimentResult = None
        if experiment_id is not None:
            if request.user.is_staff:
                if models.Experiment.objects.filter(
                    experimentId=experiment_id
                ).exists():
                    # get targets experiment_id specified in URL
                    # not JSON id, or Project ID
                    experiment = models.Experiment.objects.get(
                        experimentId=experiment_id
                    )
                    # if ExperimentResult exists, else remains None
                    if models.ExperimentResult.objects.filter(
                        experiment=experiment
                    ).exists():
                        experimentResult = models.ExperimentResult.objects.filter(
                            experiment=experiment
                        ).last()
                else:
                    return Response(
                        "An Experiment with the specified ID was not found.",
                        status=status.HTTP_404_NOT_FOUND,
                    )
            # if enduser
            else:
                if models.Experiment.objects.filter(
                    experimentId=experiment_id,
                    # filter also: Experiment belongs to user
                    user=request.user,
                ).exists():
                    experiment = models.Experiment.objects.get(
                        experimentId=experiment_id,
                    )
                    if models.ExperimentResult.objects.filter(
                        experiment=experiment
                    ).exists():
                        experimentResult = models.ExperimentResult.objects.filter(
                            experiment=experiment
                        ).last()
                else:
                    return Response(
                        "An Experiment with the specified ID was not found or does not belong to the current user.",
                        status=status.HTTP_404_NOT_FOUND,
                    )

        # this is an if statement independent from the one above
        # logic returns required status messages according to api specs
        # print(experiment)
        if experiment is not None:
            if experimentResult is not None:
                experiment_serializer = serializers.ExperimentSerializer(
                    experiment,
                )
                result_serializer = serializers.ExperimentResultGetSerializer(
                    experimentResult,
                )

                # print(experiment_serializer.data)
                return Response(
                    {
                        "experimentConfiguration": experiment_serializer.data,
                        "experimentResult": result_serializer.data,
                    },
                    status=status.HTTP_200_OK,
                )

            else:
                experiment_serializer = serializers.ExperimentSerializer(
                    experiment,
                )
                # experiment_serializer.is_valid()
                # print(experiment_serializer.data)
                return Response(
                    # {
                    #     "experimentConfiguration": experiment_serializer.data,
                    # },
                    experiment_serializer.data,
                    status=status.HTTP_200_OK,
                )
        else:
            # logic should not allow for this error to occur
            return Response(
                "Unexpected error.",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    # use patch to update status of experiment object
    # alternative: generic view + permission class isAdmin, but requires additional
    # endpoint, plus for GET this is not possiblle due to more complex logic
    def patch(self, request, experiment_id):
        """ """
        if request.user.is_staff:
            if models.Experiment.objects.filter(experimentId=experiment_id).exists():
                experiment = models.Experiment.objects.get(
                    experimentId=experiment_id)
            else:
                return Response(
                    "An Experiment with the specified ID was not found.",
                    status=status.HTTP_404_NOT_FOUND,
                )
            serializer = serializers.ExperimentSerializer(
                # Need experiment to overwrite, if experiment was missing
                # method would fail due to missing required fields.
                # Convert experiment from db to JSON and merge fields from data.
                experiment,
                data=request.data,
                partial=True,
            )
            # If the merged JSON is valid
            if serializer.is_valid():
                serializer.save()
                # print(serializer.data)
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response("Invalid data.", status=status.HTTP_400_BAD_REQUEST)

        else:
            return Response("Not allowed.", status=status.HTTP_403_FORBIDDEN)

    def delete(self, request, experiment_id):
        """ """

        if experiment_id is not None:
            if request.user.is_staff:
                if models.Experiment.objects.filter(
                    experimentId=experiment_id
                ).exists():
                    models.Experiment.objects.filter(
                        experimentId=experiment_id
                    ).delete()
                    return Response(
                        "OK - Experiment deleted successfully.",
                        status=status.HTTP_204_NO_CONTENT,
                    )
                else:
                    return Response(
                        "An Experiment with the specified ID was not found.",
                        status=status.HTTP_404_NOT_FOUND,
                    )
            else:
                if models.Experiment.objects.filter(
                    experimentId=experiment_id,
                    user=request.user,
                ).exists():
                    models.Experiment.objects.filter(
                        experimentId=experiment_id
                    ).delete()
                    return Response(
                        "OK - Experiment deleted successfully.",
                        status=status.HTTP_204_NO_CONTENT,
                    )
                else:
                    return Response(
                        "An Experiment with the specified ID was not found or does not belong to the current user.",
                        status=status.HTTP_404_NOT_FOUND,
                    )
        # 401 Authorization information is missing or invalid. is authomatically
        # handled with Django
        else:
            return Response(
                "Unexpected error.",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ExperimentListView(generics.ListCreateAPIView):
    """ """

    queryset = models.Experiment.objects.all()
    serializer_class = serializers.ExperimentSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def list(self, request):
        # Note the use of `get_queryset()` instead of `self.queryset`
        if request.user.is_staff:
            queryset = self.get_queryset()
        else:
            queryset = models.Experiment.objects.filter(user=request.user)
        serializer = serializers.ExperimentSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # need to overwrite create to save user to experiment
    # user=request.user is what the standard method doesn't do
    def create(self, request):
        data = request.data
        data["status"] = "IN QUEUE"
        serializer = serializers.ExperimentSerializer(data=data)
        # print(request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            # serializer.update(status="IN QUEUE")
            # print(serializer.data)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response("Invalid data.", status=status.HTTP_400_BAD_REQUEST)


class ExperimentResultView(APIView):
    """ """

    permission_classes = (IsAuthenticated,)
    # serializers_class = serializers.ExperimentSerializer

    def get(self, request, experiment_id):
        """ """
        experiment = None
        experimentResult = None
        if experiment_id is not None:
            if request.user.is_staff:
                if models.Experiment.objects.filter(
                    experimentId=experiment_id
                ).exists():
                    # get targets experiment_id specified in URL
                    # not JSON id, or Project ID
                    experiment = models.Experiment.objects.get(
                        experimentId=experiment_id
                    )
                    # if ExperimentResult exists, else remains None
                    if models.ExperimentResult.objects.filter(
                        experiment=experiment
                    ).exists():
                        experimentResult = models.ExperimentResult.objects.filter(
                            experiment=experiment
                        ).last()
                else:
                    return Response(
                        "An Experiment with the specified ID was not found.",
                        status=status.HTTP_404_NOT_FOUND,
                    )
            # if enduser
            else:
                if models.Experiment.objects.filter(
                    experimentId=experiment_id,
                    # filter also: Experiment belongs to user
                    user=request.user,
                ).exists():
                    experiment = models.Experiment.objects.get(
                        experimentId=experiment_id,
                    )
                    if models.ExperimentResult.objects.filter(
                        experiment=experiment
                    ).exists():
                        experimentResult = models.ExperimentResult.objects.filter(
                            experiment=experiment
                        ).last()
                else:
                    return Response(
                        "An Experiment with the specified ID was not found or does not belong to the current user.",
                        status=status.HTTP_404_NOT_FOUND,
                    )

        # this is an if statement independent from the one above
        # logic returns required status messages according to api specs
        # print(experiment)
        if experiment is not None:
            if experimentResult is not None:
                experiment_serializer = serializers.ExperimentSerializer(
                    experiment,
                )
                result_serializer = serializers.ExperimentResultPostSerializer(
                    experimentResult,
                )

                # print(experiment_serializer.data)
                return Response(result_serializer.data,
                                # {
                                #     "experimentConfiguration": experiment_serializer.data,
                                #     "experimentResult": result_serializer.data,
                                # },
                                status=status.HTTP_200_OK,
                                )

            else:
                experiment_serializer = serializers.ExperimentSerializer(
                    experiment,
                )
                # experiment_serializer.is_valid()
                # print(experiment_serializer.data)
                return Response(
                    # {
                    #     "experimentConfiguration": experiment_serializer.data,
                    # },
                    experiment_serializer.data,
                    status=status.HTTP_200_OK,
                )
        else:
            # logic should not allow for this error to occur
            return Response(
                "Unexpected error.",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    # use patch to update status of experiment object
    # alternative: generic view + permission class isAdmin, but requires additional
    # endpoint, plus for GET this is not possiblle due to more complex logic
    def patch(self, request, experiment_id):
        """ """
        if request.user.is_staff:
            if models.Experiment.objects.filter(experimentId=experiment_id).exists():
                experiment = models.Experiment.objects.get(
                    experimentId=experiment_id)
            else:
                return Response(
                    "An Experiment with the specified ID was not found.",
                    status=status.HTTP_404_NOT_FOUND,
                )
            serializer = serializers.ExperimentSerializer(
                # Need experiment to overwrite, if experiment was missing
                # method would fail due to missing required fields.
                # Convert experiment from db to JSON and merge fields from data.
                experiment,
                data=request.data,
                partial=True,
            )
            # If the merged JSON is valid
            if serializer.is_valid():
                serializer.save()
                # print(serializer.data)
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response("Invalid data.", status=status.HTTP_400_BAD_REQUEST)

        else:
            return Response("Not allowed.", status=status.HTTP_403_FORBIDDEN)

    def delete(self, request, experiment_id):
        """ """

        if experiment_id is not None:
            if request.user.is_staff:
                if models.Experiment.objects.filter(
                    experimentId=experiment_id
                ).exists():
                    models.Experiment.objects.filter(
                        experimentId=experiment_id
                    ).delete()
                    return Response(
                        "OK - Experiment deleted successfully.",
                        status=status.HTTP_204_NO_CONTENT,
                    )
                else:
                    return Response(
                        "An Experiment with the specified ID was not found.",
                        status=status.HTTP_404_NOT_FOUND,
                    )
            else:
                if models.Experiment.objects.filter(
                    experimentId=experiment_id,
                    user=request.user,
                ).exists():
                    models.Experiment.objects.filter(
                        experimentId=experiment_id
                    ).delete()
                    return Response(
                        "OK - Experiment deleted successfully.",
                        status=status.HTTP_204_NO_CONTENT,
                    )
                else:
                    return Response(
                        "An Experiment with the specified ID was not found or does not belong to the current user.",
                        status=status.HTTP_404_NOT_FOUND,
                    )
        # 401 Authorization information is missing or invalid. is authomatically
        # handled with Django
        else:
            return Response(
                "Unexpected error.",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ExperimentQueueView(generics.RetrieveUpdateAPIView):
    """ """

    queryset = models.Experiment.objects.filter(status="IN QUEUE")
    serializer_class = serializers.ExperimentSerializer
    permission_classes = [
        IsAdminUser,
    ]

    def retrieve(self, request):
        # if no object with status "IN QUEUE" exists returns null fields
        queryset = models.Experiment.objects.filter(status="IN QUEUE").first()
        serializer = serializers.ExperimentSerializer(queryset, many=False)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ExperimentDataView(generics.RetrieveAPIView):
    """ """

    def retrieve(self, request, experiment_id):
        if models.Experiment.objects.filter(
            experimentId=experiment_id
        ).exists():
            queryset = models.Experiment.objects.filter(
                experimentId=experiment_id
            )
            serializer = serializers.ExperimentDataSerializer(
                queryset, many=False)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(
                "An Experiment with the specified ID was not found.",
                status=status.HTTP_404_NOT_FOUND,
            )


# only needs to handle create-request from admin
class ResultView(generics.ListCreateAPIView):
    queryset = models.ExperimentResult.objects.all()
    serializer_class = serializers.ExperimentResultPostSerializer
    permission_classes = [
        IsAdminUser,
    ]


class ResultDetailView(generics.RetrieveDestroyAPIView):
    queryset = models.ExperimentResult.objects.all()
    serializer_class = serializers.ExperimentResultPostSerializer
    permission_classes = [
        IsAdminUser,
    ]


class RegisterView(generics.CreateAPIView):
    queryset = models.UserProfile.objects.all()
    serializer_class = serializers.UserProfileSerializer


class UserLoginApiView(KnoxLoginView):
    """Handle creating user authentication tokens"""

    # renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES
    permission_classes = (AllowAny,)

    def post(self, request, format=None):
        serializer = AuthTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        userId = user.id
        userEmail = user.email
        userName = user.name
        # create session based auth with token auth
        login(request, user)
        temp_list = super(UserLoginApiView, self).post(request, format=None)
        temp_list.data["id"] = userId
        temp_list.data["email"] = userEmail
        temp_list.data["name"] = userName

        return Response(temp_list.data)


class UserUpdateView(generics.UpdateAPIView):
    queryset = models.UserProfile.objects.all()
    serializer_class = serializers.UserProfileSerializer
    permission_classes = [
        IsAuthenticated,
        UpdateOwnProfile,
    ]
