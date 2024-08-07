from rest_framework import serializers
from .models import Borrowing, Payment
from book.serializers import BookSerializer
from user.serializers import UserSerializer


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            "status", "type",
            "session_url", "session_id",
            "money_to_pay"
        ]


class BorrowingSerializer(serializers.ModelSerializer):
    book = BookSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)

    class Meta:
        model = Borrowing
        fields = [
            "id", "user", "book",
            "borrow_date", "expected_return_date",
            "actual_return_date", "payments"
        ]
        read_only_fields = ["expected_return_date", "actual_return_date"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.actual_return_date:
            data['payments'] = PaymentSerializer(instance.payments.all(), many=True).data
        return data


class BorrowingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Borrowing
        fields = ["book", "expected_return_date", "user"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if not request.user.is_staff:
            self.fields.pop('user', None)

    def validate_book(self, value):
        if value.inventory == 0:
            raise serializers.ValidationError(
                "This book is not available for borrowing."
            )
        return value

    def create(self, validated_data):
        user = validated_data.pop('user', self.context["request"].user)
        book = validated_data["book"]
        book.inventory -= 1
        book.save()
        borrowing = Borrowing.objects.create(user=user, **validated_data)

        return borrowing