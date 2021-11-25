from django.contrib import admin
from cdl_rest_api import models

admin.register(models.Experiment)
admin.register(models.UserProfile)
admin.register(models.ExperimentResult)
