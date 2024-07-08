from rest_framework import serializers

from .models import Game


class GameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Game
        fields = "__all__"


class CSVURLSerializer(serializers.Serializer):
    url = serializers.URLField()
