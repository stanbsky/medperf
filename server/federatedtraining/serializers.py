from rest_framework import serializers
from django.utils import timezone
from .models import FederatedTraining


class FederatedTrainingSerializer(serializers.ModelSerializer):
    class Meta:
        model = FederatedTraining
        fields = "__all__"
        read_only_fields = ["owner", "approved_at", "approval_status"]

    def validate(self, data):
        owner = self.context["request"].user
        pending_trainings = FederatedTraining.objects.filter(
            owner=owner, approval_status="PENDING"
        )
        if len(pending_trainings) > 0:
            raise serializers.ValidationError(
                "User can own at most one pending federated training"
            )

        # if "state" in data and data["state"] == "OPERATION":
        #     dev_mlcubes = [
        #         data["data_preparation_mlcube"].state == "DEVELOPMENT",
        #         data["reference_model_mlcube"].state == "DEVELOPMENT",
        #         data["data_evaluator_mlcube"].state == "DEVELOPMENT",
        #     ]
        #     if any(dev_mlcubes):
        #         raise serializers.ValidationError(
        #             "User cannot mark a federated training as operational"
        #             " if its MLCubes are not operational"
        #         )

        return data


class FederatedTrainingApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = FederatedTraining
        read_only_fields = ["owner", "approved_at"]
        fields = "__all__"

    def update(self, instance, validated_data):
        if "approval_status" in validated_data:
            if validated_data["approval_status"] != instance.approval_status:
                instance.approval_status = validated_data["approval_status"]
                if instance.approval_status != "PENDING":
                    instance.approved_at = timezone.now()
        validated_data.pop("approval_status", None)
        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()
        return instance

    def validate_approval_status(self, approval_status):
        if approval_status == "PENDING":
            raise serializers.ValidationError(
                "User can only approve or reject a federated training"
            )
        if self.instance.state == "DEVELOPMENT":
            raise serializers.ValidationError(
                "User cannot approve or reject when federated training is in development stage"
            )

        if approval_status == "APPROVED":
            if self.instance.approval_status == "REJECTED":
                raise serializers.ValidationError(
                    "User can approve only a pending request"
                )
        return approval_status

    # def validate_state(self, state):
    #     if state == "OPERATION" and self.instance.state != "OPERATION":
    #         dev_mlcubes = [
    #             self.instance.data_preparation_mlcube.state == "DEVELOPMENT",
    #             self.instance.reference_model_mlcube.state == "DEVELOPMENT",
    #             self.instance.data_evaluator_mlcube.state == "DEVELOPMENT",
    #         ]
    #         if any(dev_mlcubes):
    #             raise serializers.ValidationError(
    #                 "User cannot mark a benchmark as operational"
    #                 " if its MLCubes are not operational"
    #             )
    #     return state

    def validate(self, data):
        if self.instance.state == "OPERATION":
            editable_fields = [
                "is_valid",
                "is_active",
                "user_metadata",
                "approval_status",
                # "demo_dataset_tarball_url",
            ]
            for k, v in data.items():
                if k not in editable_fields:
                    if v != getattr(self.instance, k):
                        raise serializers.ValidationError(
                            "User cannot update non editable fields in Operation mode"
                        )
        return data
