from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register

from cdl_rest_api import models


class UserProfileAdmin(ModelAdmin):
    model = models.UserProfile


class ExperimentAdmin(ModelAdmin):
    model = models.Experiment


class ExperimentResultAdmin(ModelAdmin):
    model = models.ExperimentResult


modeladmin_register(UserProfileAdmin)
modeladmin_register(ExperimentAdmin)
modeladmin_register(ExperimentResultAdmin)
