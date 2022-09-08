from rest_framework import serializers

from cdl_rest_api import models

# from django.contrib.auth.models import User


class QubitMeasurementItemSerializer(serializers.ModelSerializer):
    """
    Serializer for the QubitMeasurementItem
    """

    class Meta:
        model = models.QubitMeasurementItem
        fields = "__all__"


class CircuitConfigurationItemSerializer(serializers.ModelSerializer):
    """
    Serializer for the CircuitConfigruationItem
    """

    class Meta:
        model = models.CircuitConfigurationItem
        fields = "__all__"


class clusterStateSerializer(serializers.ModelSerializer):
    """
    Serializer for the clusterState model
    """

    choices = ["linear", "ghz"]
    presetSettings = serializers.ChoiceField(choices)

    class Meta:
        model = models.clusterState
        fields = "__all__"


class qubitComputingSerializer(serializers.ModelSerializer):
    """
    Serializer for qubitComputing model
    """

    # To Do: Cluster state configurations need to be added here
    # choices = [
    #     "horseshoe",
    # ]
    # circuitConfiguration = serializers.ChoiceField(choices)
    # assigns array of CircuitConfigurationItems for GET
    circuitAngles = CircuitConfigurationItemSerializer(many=True)

    def create(self, validated_data):
        """
        create function for qubitComputingSerializer handles the array type of
        the circuitAngles field. circuitAngles is an array of
        CircuitConfigurationItems.
        """
        # remove circuitAngles array from validated_data and store it in
        # circuitAnglesData
        circuitAnglesData = validated_data.pop("circuitAngles")
        # create qubitComputing database entry
        qubitComputing = models.qubitComputing.objects.create(**validated_data)
        # for each pair of Angle + Value, create CircuitConfigurationItem with
        # ForeignKey = qubitComputing that has been created
        for circuitAngle in circuitAnglesData:
            models.CircuitConfigurationItem.objects.create(
                # ** interchanges a dict to a tuple
                # object qubitComputing needs be created before being referenced
                qubitComputing=qubitComputing,
                **circuitAngle
            )
        return qubitComputing

    class Meta:
        # no depth argument since no ForeignKey in model
        model = models.qubitComputing
        fields = "__all__"


class ComputeSettingsSerializer(serializers.ModelSerializer):
    """
    Serializer for the ComputeSettings model
    """

    qubitComputing = qubitComputingSerializer()
    clusterState = clusterStateSerializer()
    encodedQubitMeasurements = QubitMeasurementItemSerializer(many=True)

    def create(self, validated_data):
        """
        create function for ComputeSettingsSerializer handles the array type of
        the encodedQubitMeasurements field. encodedQubitMeasurements is an array
        of QubitMeasurementItems.
        """
        encodedQubitMeasurementsData = validated_data.pop(
            "encodedQubitMeasurements")
        qubitComputingData = validated_data.pop("qubitComputing")
        # pass qubitComputing to qubitComputingSerializer
        serializer = qubitComputingSerializer(data=qubitComputingData)
        serializer.is_valid()
        qubitComputing = serializer.save()
        clusterStateData = validated_data.pop("clusterState")
        clusterState = models.clusterState.objects.create(**clusterStateData)
        ComputeSettings = models.ComputeSettings.objects.create(
            clusterState=clusterState, qubitComputing=qubitComputing
        )
        for encodedQubitMeasurement in encodedQubitMeasurementsData:
            models.QubitMeasurementItem.objects.create(
                ComputeSettings=ComputeSettings, **encodedQubitMeasurement
            )
        return ComputeSettings

    class Meta:
        model = models.ComputeSettings
        fields = ("encodedQubitMeasurements", "qubitComputing", "clusterState")
        # return entire object of ForeignKey assignment not just id
        depth = 1


class ExperimentSerializer(serializers.ModelSerializer):
    """
    Serializer for the Experiment model
    """

    ComputeSettings = ComputeSettingsSerializer()
    user_id = serializers.ReadOnlyField()
    experimentId = serializers.ReadOnlyField()

    def create(self, validated_data):
        """
        create function for ExperimentSerializer handles the ForeignKey
        relation between Experiment and ComputeSettings (1 Experiment has
        1 Compute Setting)
        """
        print(validated_data)
        computeSettingsData = validated_data.pop("ComputeSettings")
        # codes lines reversed compared to above
        # Foreign Key is in Experiment, not ComputeSettings
        # pass ComputeSettings to ComputeSettingsSerializer
        serializer = ComputeSettingsSerializer(data=computeSettingsData)
        serializer.is_valid()
        # print(serializer.errors)
        computeSetting = serializer.save()
        # ComputeSettings is created in the ComputeSettingsSerializer
        Experiment = models.Experiment.objects.create(
            ComputeSettings=computeSetting, **validated_data
        )
        return Experiment

    # custom update function is needed to update nested models.

    class Meta:
        model = models.Experiment
        fields = (
            # object Experiment has no Database ID
            "user_id",
            "status",
            "created",
            "experimentName",
            "projectId",
            "maxRuntime",
            "experimentId",
            "circuitId",
            "ComputeSettings",
        )
        depth = 1


class CountratesSerializer(serializers.ModelSerializer):
    """
    Serializer for Countrates model
    """

    class Meta:
        model = models.Countrates
        fields = ("d1", "d2", "d3", "d4", "d5", "d6", "d7", "d8")


class ExperimentDataSerializer(serializers.ModelSerializer):
    """
    Serializer for ExperimentData model
    """

    # field contains one Countrates object
    countratePerDetector = CountratesSerializer()

    def create(self, validated_data):
        """
        create function for ExperimentDataSerializer handles ForeignKey relations
        of ExperimentData with Countrates and Coincidences
        """

        countratesData = validated_data.pop("countratePerDetector")
        serializer = CountratesSerializer(data=countratesData)
        serializer.is_valid()
        countrates = serializer.save()
        coincidences = validated_data.pop("coincidenceCounts")
        ExperimentData = models.ExperimentData.objects.create(
            countratePerDetector=countrates, coincidenceCounts=coincidences
        )

        return ExperimentData

    class Meta:
        model = models.ExperimentData
        fields = ("countratePerDetector", "coincidenceCounts")
        # return entire object of ForeignKey assignment not just id
        depth = 1


class ExperimentResultPostSerializer(serializers.ModelSerializer):
    """ """

    experimentData = ExperimentDataSerializer()

    def create(self, validated_data):
        experimentData = validated_data.pop("experimentData")
        # codes lines reversed compared to above
        # Foreign Key is in Experiment, not ComputeSettings
        # 1 Experiment has 1 Compute Setting
        serializer = ExperimentDataSerializer(data=experimentData)
        serializer.is_valid()
        # print(serializer.errors)
        experimentData = serializer.save()
        Experiment = models.ExperimentResult.objects.create(
            experimentData=experimentData, **validated_data
        )
        return Experiment

    class Meta:
        model = models.ExperimentResult
        fields = (
            "experiment",
            "startTime",
            "totalCounts",
            "numberOfDetectors",
            "singlePhotonRate",
            "totalTime",
            "experimentData",
        )


class ExperimentResultGetSerializer(serializers.ModelSerializer):
    """ """

    # experimentData = ExperimentDataSerializer()

    def create(self, validated_data):
        experimentData = validated_data.pop("experimentData")
        # codes lines reversed compared to above
        # Foreign Key is in Experiment, not ComputeSettings
        # 1 Experiment has 1 Compute Setting
        serializer = ExperimentDataSerializer(data=experimentData)
        serializer.is_valid()
        # print(serializer.errors)
        experimentData = serializer.save()
        Experiment = models.ExperimentResult.objects.create(
            experimentData=experimentData, **validated_data
        )
        return Experiment

    class Meta:
        model = models.ExperimentResult
        fields = (
            "experiment",
            "startTime",
            "totalCounts",
            "numberOfDetectors",
            "singlePhotonRate",
            "totalTime",
        )  # , "experimentData")


# User Serializer


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializes a user profile object"""

    # ModelSerializer uses Meta class to configure the serializers
    # to point to a specific model
    class Meta:
        # model = User
        model = models.UserProfile
        fields = ("id", "email", "name", "password")
        # Extra keyword args
        extra_kwargs = {
            "password": {
                # Can only create new or update objects
                # Get request will not include password field in its response
                "write_only": True,
                # Hide input while typing
                "style": {"input_type": "password"},
            }
        }

    # Overwrite the create function and call create_user function
    def create(self, validated_data):
        """Create and return a new user"""
        user = models.UserProfile.objects.create_user(
            email=validated_data["email"],
            name=validated_data["name"],
            password=validated_data["password"],
        )

        return user

    def update(self, instance, validated_data):
        """Handle updating user account"""
        if "password" in validated_data:
            password = validated_data.pop("password")
            instance.set_password(password)

        return super().update(instance, validated_data)
