from rest_framework import serializers

class TaskSerializer(serializers.Serializer):
    id = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    title = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    due_date = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    estimated_hours = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    importance = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    dependencies = serializers.ListField(
        child=serializers.CharField(allow_null=True, allow_blank=True),
        required=False,
        allow_empty=True
    )
