from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.models import BaseUserManager
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator

import uuid


class QubitMeasurementItem(models.Model):
    """
    Represents the Qubit Measurement Settings and contains values for
    projection onto the computational basis |0> and |1>:
    |psi> = cos(theta)|0> + exp(i*phi)|1>
    """

    # Qubit Index
    encodedQubitIndex = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1),
        ],
        blank=True,
        null=True,
    )

    # angle theta
    theta = models.DecimalField(
        validators=[
            MinValueValidator(0),
            MaxValueValidator(360),
        ],
        decimal_places=2,
        max_digits=5,
        blank=True,
        null=True,
    )

    # angle phi
    phi = models.DecimalField(
        validators=[
            MinValueValidator(0),
            MaxValueValidator(360),
        ],
        decimal_places=2,
        max_digits=5,
        blank=True,
        null=True,
    )

    # QubitMeasurementItem is related to ComputeSettings
    # ComputeSettings object contains an array of QubitMeasurementItems in the
    # field named encodedQubitMeasurements
    ComputeSettings = models.ForeignKey(
        "ComputeSettings",
        # CASCADE? ComputeSettings should'nt be deleted when
        # encodedQubitMeasurements Item is deleted
        # Set the ForeignKey null; this is only possible if null is True
        on_delete=models.SET_NULL,
        null=True,
        # related_name specifies the name of the reverse relation from the
        # ComputeSettings model back to QubitMeasurementItem model,
        # i.e. specifies how field is named in ForeignKey model
        related_name="encodedQubitMeasurements",
    )


class CircuitConfigurationItem(models.Model):
    """
    Contains names and values for abstract circuit gate operations
    R_z(circuitAngleName) = circuitAngleValue
    """

    # specifies the name of the angle, e.g. "alpha"
    circuitAngleName = models.CharField(max_length=255)
    # specifies the value of the angle
    circuitAngleValue = models.DecimalField(
        validators=[
            MinValueValidator(0),
            MaxValueValidator(360),
        ],
        decimal_places=3,
        max_digits=6,
    )
    # relates gate operations to qubitComputing model which contains an array
    # of CircuitConfigurationItems in related name field "circuitAngles" as
    # well as the circuitConfiguration implied by the cluster, "horseshoe" etc.
    qubitComputing = models.ForeignKey(
        "qubitComputing",
        on_delete=models.SET_NULL,
        null=True,
        related_name="circuitAngles",
    )


class clusterState(models.Model):
    """
    Defines the number of physical qubits and shape of the cluster
    """

    amountQubits = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(4),
        ]
    )
    # defines the cluster state e.g. "linear" or "ghz" and is validated against
    # choices in serializer
    presetSettings = models.CharField(max_length=255)


class qubitComputing(models.Model):
    """
    Combines all abstract circuit settings and has two fields:

    cirucitConfiguration: is defined below in the model

    circuitAngles: is an array of CircuitConfigurationItem objects
    which is handled in the qubitComputingSerializer
    """

    # the circuitConfiguration implied by the cluster, "horseshoe" etc.
    # choices are handles in the qubitComputingSerializer
    circuitConfiguration = models.CharField(max_length=255)


class ComputeSettings(models.Model):
    """
    Combines all parameters relevant for computation and has three fields:

    clusterState: specified below in the model

    qubitComputing: specified below in the model

    encodedQubitMeasurements: is an array of QubitMeasurementItem objects
    which is handled in the ComputeSettingsSerializer
    """

    # defined by clusterState model
    clusterState = models.ForeignKey(
        "clusterState",
        on_delete=models.SET_NULL,
        null=True,
    )
    # consists of enum field and array which are handled in ComputeSettingsSerializer
    qubitComputing = models.ForeignKey(
        "qubitComputing",
        on_delete=models.SET_NULL,
        null=True,
    )


class ExperimentBase(models.Model):
    """
    Contains all fields of an Experiment that can be specified by the user
    """

    # the user can give a name to the experiment
    experimentName = models.CharField(max_length=255)
    # the circuit ID is defined by the choice of the geometry of the cluster
    # and identifies the corresponding circuit in the backend
    circuitId = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(22),
        ],
    )
    # the user can associate a project ID to the experiment
    projectId = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )
    # users can specifiy how long they will use the system
    maxRuntime = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(120),
        ],
        blank=True,
        null=True,
        # set default Runtime to 5 seconds
        default=5,
    )
    # ExperimentBase model contains an entire ComputeSettings object
    ComputeSettings = models.ForeignKey(
        "ComputeSettings",
        on_delete=models.SET_NULL,
        null=True,
    )


class Experiment(ExperimentBase):
    """
    Defines additional fields set by the server with ExperimentBase
    as parent class
    """

    # specifies possible values for status field
    statusChoices = (
        ("INITIAL", "Initial"),
        ("IN QUEUE", "In Queue"),
        ("RUNNING", "Running"),
        ("FAILED", "Failed"),
        ("DONE", "Done"),
    )
    # experiment ID is set by the server
    experimentId = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )

    status = models.CharField(
        max_length=255, choices=statusChoices, null=True, blank=True
    )
    # Relates an Experiment object to a user, who can have multiple Experiments.
    # Currently this only implemented in Experiment and not in Results as
    # Result is related to an Experiment (this can be changed later to
    # assign Results to user if needed).
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
    )


class ExperimentResult(models.Model):
    """
    This model defines a Result to a corresponding Experiment
    """

    startTime = models.DateTimeField(auto_now_add=True)
    totalCounts = models.PositiveIntegerField()
    numberOfDetectors = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(8),
        ]
    )
    singlePhotonRate = models.DecimalField(
        decimal_places=2,
        max_digits=8,
    )
    totalTime = models.PositiveIntegerField()
    experiment = models.ForeignKey(
        "Experiment",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )


# User Manager class tells Django how to work with the customized
# user model in CLI. By default when a user is created it expects
# a username and a password field but the username field has been
# replaceed with an email field so a custom User Manager is needed.
class UserProfileManager(BaseUserManager):
    """
    Manager for user profiles with BaseUserManager as parent class.
    Functions within this class are used to manipulate objects
    within the model that the manager is for.
    """

    def create_user(self, email, name, password=None):
        """Create a new user profile"""
        # Case when email is either empty string or null value: Raise exception
        if not email:
            raise ValueError("Users must have an email address")

        email = self.normalize_email(email)
        # By default self.model is set to the model that the manager is for
        user = self.model(email=email, name=name)
        # Use set_password function that comes with user model
        # Makes sure the password is stored as hash in database
        user.set_password(password)
        # Standard procedure for saving objects in Django
        user.save(using=self._db)

        return user

    def create_superuser(self, email, name, password):
        """Create and save a new superuser with given details"""
        # Self is automatically passed in for any class functions
        # When it is called from a different function or a different part
        user = self.create_user(email, name, password)

        # is_superuser is automatically created by PermissionsMixin
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)

        return user


class UserProfile(AbstractBaseUser, PermissionsMixin):
    """Database model for user in the system"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Define various fields that model should provide:
    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    # Determines fields for the permission system
    is_active = models.BooleanField(default=True)
    # Determines acces to Django admin
    is_staff = models.BooleanField(default=False)
    # Specify model manager:
    # This is required because the custom user model is used with
    # the Django CLI
    objects = UserProfileManager()

    # Overwriting the default USERNAME_FIELD which is normally user name
    # and replacing it with email field
    # When users authenticate they provide email address and pw
    USERNAME_FIELD = "email"
    # Adding username to additional REQUIRED_FIELDS
    REQUIRED_FIELDS = ["name"]

    def get_full_name(self):
        """Retrieve full name of user"""
        return self.name

    def get_short_name(self):
        """Retrieve short name of user"""
        return self.name

    # Converting a user profile object into a string
    def __str__(self):
        """Return string representation of our user"""
        # String representation is email address
        return self.email
