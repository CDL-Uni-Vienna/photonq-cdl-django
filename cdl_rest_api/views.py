
from rest_framework import generics, status
# from rest_framework.settings import api_settings
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response  # Standard Response object
from rest_framework.views import APIView

from cdl_rest_api import models, serializers
from cdl_rest_api.permissions import OriginAuthenticated, UpdateOwnProfile


# Multiple endpoints for detail view and list view
# Alternative: implement primary key in one endpoint logic
class ExperimentDetailView(APIView):
    """
    This View returns one Experiment object with pk = experiment_id
    """

    permission_classes = (OriginAuthenticated,)
    # serializers_class = serializers.ExperimentSerializer

    def get(self, request, experiment_id):
        """
        GET function for ExperimentDetailView
        """

        experiment = None
        experimentResult = None
        if experiment_id is not None:
            if request.origin_user.is_staff:
                # if Experiment exists, else remain None
                if models.Experiment.objects.filter(
                    experimentId=experiment_id
                ).exists():
                    # get targets experiment_id specified in URL
                    # not JSON id, or Project ID
                    experiment = models.Experiment.objects.get(
                        experimentId=experiment_id
                    )
                    # if Experiment Result for Experiment exists
                    if models.ExperimentResult.objects.filter(
                        experiment=experiment
                    ).exists():
                        # one Experiment can have multiple results, and only
                        # the latest is returned in the view response
                        experimentResult = models.ExperimentResult.objects.filter(
                            # experiment is a ForeignKey in ExperimentResult model
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
                    # additional filter: Experiment belongs to user
                    user_id=request.origin_user.id,
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

        # this is an if statement independent from the one above:
        # logic returns required status messages according to api specs
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
                    experiment_serializer.data,
                    status=status.HTTP_200_OK,
                )
        else:
            # logic should not allow for this error to occur
            return Response(
                "Unexpected error.",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    # use patch to update status field of experiment object
    # alternative: generic view + permission class isAdmin, but requires additional
    # endpoint, plus for GET this is hard to implement due to complex logic for GET
    def patch(self, request, experiment_id):
        """
        PATCH function for ExperimentDetailView
        """

        if request.origin_user.is_staff:
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
            # if the merged JSON is valid
            if serializer.is_valid():
                serializer.save()
                # print(serializer.data)
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response("Invalid data.", status=status.HTTP_400_BAD_REQUEST)

        else:
            return Response(
                "Please authenticate as admin user to update ExperimentResult objects.",
                status=status.HTTP_403_FORBIDDEN,
            )

    def delete(self, request, experiment_id):
        """
        DELETE function for ExperimentDetailView
        """

        if experiment_id is not None:
            if request.origin_user.is_staff:
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
                    user_id=request.origin_user.id,
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
        # 401 Authorization information is missing or invalid is authomatically
        # handled with Django
        # TO DO: is this the right response here?
        else:
            return Response(
                "Unexpected error.",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ExperimentListView(generics.ListCreateAPIView):
    """
    This view returns all existing Experiment objects to the super user
    and all Experiments that belong to the authenticated user for end user
    """

    # a QuerySet can be constructed, filtered, sliced, and generally passed
    # around without actually hitting the database. No database activity
    # actually occurs until you do something to evaluate the queryset
    queryset = models.Experiment.objects.all()
    serializer_class = serializers.ExperimentSerializer
    permission_classes = [
        OriginAuthenticated,
    ]

    def list(self, request):
        # Note the use of `get_queryset()` instead of `self.queryset`
        if request.origin_user.is_staff:
            queryset = self.get_queryset()
        else:
            queryset = models.Experiment.objects.filter(
                user_id=request.origin_user)
        serializer = serializers.ExperimentSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # need to overwrite create to save user to experiment
    # user_id=request.origin_user.id is what the standard method doesn't do
    def create(self, request):
        data = request.data
        # overwrites status field in view
        # cleaner alternative: set default in model
        # leave for now
        data["status"] = "IN QUEUE"
        serializer = serializers.ExperimentSerializer(data=data)
        # print(request.data)
        if serializer.is_valid():
            serializer.save(user_id=request.origin_user.id)
            # print(serializer.data)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response("Invalid data.", status=status.HTTP_400_BAD_REQUEST)


class ExperimentResultView(APIView):
    """
    This view returns the latest ExperimentResult object for a given Experiment
    and is logically equivalent to ExperimentDetailView
    """

    permission_classes = (IsAuthenticated,)
    # serializers_class = serializers.ExperimentSerializer

    def get(self, request, experiment_id):
        """
        GET function for ExperimentResultView
        """
        experiment = None
        experimentResult = None
        if experiment_id is not None:
            # retrieve data from db and store in experiment and
            # experimentResult variables:
            # if staff user
            if request.origin_user.is_staff:
                if models.Experiment.objects.filter(
                    experimentId=experiment_id
                ).exists():
                    # get targets experiment_id specified in URL
                    # not JSON id, or Project ID (see urls.py)
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
                    user_id=request.origin_user.id,
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

        # this if statement is independent from the one above, and applies only
        # if and experiment has been identified:
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
                return Response(
                    result_serializer.data,
                    # {
                    #     "experimentConfiguration": experiment_serializer.data,
                    #     "experimentResult": result_serializer.data,
                    # },
                    status=status.HTTP_200_OK,
                )
            # TO DO: Here some more logic is needed: currently experiment
            # object is returned in case no result is available
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

    def delete(self, request, experiment_id):
        """
        DELETE function for ExperimentResultView
        """
        # TO DO: this Endpoint still needs to be adjusted to Result
        # currently user deletes Experiment not Result
        # TO DO: check if obsolete due to ResultDetailView endpoint
        if experiment_id is not None:
            if request.origin_user.is_staff:
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
                    user_id=request.origin_user.id,
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
    """
    This view returns the latest Experiment object in the queue
    """

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


# TO DO: check if obsolete
class ExperimentDataView(generics.RetrieveAPIView):
    """ """

    def retrieve(self, request, experiment_id):
        if models.Experiment.objects.filter(experimentId=experiment_id).exists():
            queryset = models.Experiment.objects.filter(
                experimentId=experiment_id)
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
    """
    This view enables admin user to post new results and all list existing results
    """

    queryset = models.ExperimentResult.objects.all()
    serializer_class = serializers.ExperimentResultPostSerializer
    permission_classes = [
        IsAdminUser,
    ]


# TO DO: check against delete function in ExperimentResultView
class ResultDetailView(generics.RetrieveDestroyAPIView):
    """ """

    queryset = models.ExperimentResult.objects.all()
    serializer_class = serializers.ExperimentResultPostSerializer
    permission_classes = [
        IsAdminUser,
    ]


class RegisterView(generics.CreateAPIView):
    """
    This view allows unauthenticated users to create a user profile
    """

    queryset = models.UserProfile.objects.all()
    serializer_class = serializers.UserProfileSerializer


class UserUpdateView(generics.UpdateAPIView):
    queryset = models.UserProfile.objects.all()
    serializer_class = serializers.UserProfileSerializer
    permission_classes = [
        IsAuthenticated,
        UpdateOwnProfile,
    ]
