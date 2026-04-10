from rest_framework import serializers
from .models import InternOffer, Application, Report


class InternOfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = InternOffer
        fields = "__all__"


class ApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = "__all__"


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = "__all__"
