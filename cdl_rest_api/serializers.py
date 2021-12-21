from rest_framework import serializers

# from django.contrib.auth.models import User

from cdl_rest_api import models


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
    """ """

    # To Do: Cluster state configurations need to be added here
    choices = [
        "horseshoe",
    ]
    circuitConfiguration = serializers.ChoiceField(choices)
    # assigns array of CircuitConfigurationItems for GET
    circuitAngles = CircuitConfigurationItemSerializer(many=True)

    def create(self, validated_data):
        """ """
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
    """ """

    qubitComputing = qubitComputingSerializer()
    clusterState = clusterStateSerializer()
    encodedQubitMeasurements = QubitMeasurementItemSerializer(many=True)

    def create(self, validated_data):
        """ """
        encodedQubitMeasurementsData = validated_data.pop(
            "encodedQubitMeasurements")
        qubitComputingData = validated_data.pop("qubitComputing")
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
    """ """

    ComputeSettings = ComputeSettingsSerializer()
    user = serializers.ReadOnlyField(source="user.email")
    experimentId = serializers.ReadOnlyField()

    # choices = ["IN QUEUE", "RUNNING", "FAILED", "DONE"]
    # status = serializers.ChoiceField(choices)

    def create(self, validated_data):
        computeSettingsData = validated_data.pop("ComputeSettings")
        # codes lines reversed compared to above
        # Foreign Key is in Experiment, not ComputeSettings
        # 1 Experiment has 1 Compute Setting
        serializer = ComputeSettingsSerializer(data=computeSettingsData)
        serializer.is_valid()
        # print(serializer.errors)
        computeSetting = serializer.save()
        Experiment = models.Experiment.objects.create(
            ComputeSettings=computeSetting, **validated_data
        )
        return Experiment

    # custom update function is needed to update nested models.

    class Meta:
        model = models.Experiment
        fields = (
            # object Experiment has no Database ID
            "user",
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
    """ """
    class Meta:
        model = models.Countrates
        fields = ("d1", "d2", "d3", "d4", "d5", "d6", "d7", "d8")


class CoincidencesSerializer(serializers.ModelSerializer):
    """ """
    class Meta:
        model = models.Coincidences
        fields = ("c00", "c01", "c10", "c11")


class ExperimentDataSerializer(serializers.ModelSerializer):
    """ """
    countratePerDetector = CountratesSerializer()
    encodedQubitMeasurements = CoincidencesSerializer()

    def create(self, validated_data):
        """ """

        countratesData = validated_data.pop("countratePerDetector")
        serializer = CountratesSerializer(data=countratesData)
        serializer.is_valid()
        countrates = serializer.save()
        coincidencesData = validated_data.pop("encodedQubitMeasurements")
        coincidences = models.Coincidences.objects.create(**coincidencesData)
        ExperimentData = models.ExperimentData.objects.create(
            countratePerDetector=countrates, encodedQubitMeasurements=coincidences
        )

        return ExperimentData

    class Meta:
        model = models.ExperimentData
        fields = ("countratePerDetector", "encodedQubitMeasurements")
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
        fields = ("experiment", "startTime", "totalCounts",
                  "numberOfDetectors", "singlePhotonRate", "totalTime", "experimentData")


class ExperimentResultGetSerializer(serializers.ModelSerializer):
    """ """
    #experimentData = ExperimentDataSerializer()

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
        fields = ("experiment", "startTime", "totalCounts",
                  "numberOfDetectors", "singlePhotonRate", "totalTime")  # , "experimentData")

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
