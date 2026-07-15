"""Reservation serializers — List/Detail selectordan (nested dict) keladigan
ma'lumot bilan ishlaydi, Write esa serializer validatsiyasidan keyin service'ga
yo'naltiradi (ORM, Reservation instance qaytaradi)."""

from rest_framework import serializers

from apps.reservation.models import Reservation
from apps.reservation.services import create_reservation, cancel_reservation


class RoomTypeShortSerializer(serializers.Serializer):
    """Selectordan kelgan nested room_type dict uchun (swagger uchun ham kerak)."""
    id = serializers.IntegerField()
    name = serializers.CharField()
    base_price = serializers.DecimalField(max_digits=10, decimal_places=2)


class AssignedRoomShortSerializer(serializers.Serializer):
    """Selectordan kelgan nested assigned_room dict uchun."""
    id = serializers.IntegerField()
    number = serializers.CharField()


class ReservationListSerializer(serializers.Serializer):
    """List/swagger uchun — selector natijasi (dict) bilan ishlaydi, ModelSerializer emas."""
    id = serializers.IntegerField()
    guest_name = serializers.CharField()
    room_type = RoomTypeShortSerializer()
    status = serializers.ChoiceField(choices=Reservation.Status.choices)
    check_in_date = serializers.DateField()
    check_out_date = serializers.DateField()
    created_at = serializers.DateTimeField()


class ReservationDetailSerializer(serializers.Serializer):
    """Retrieve uchun — selector (dict) va service (ORM instance) ikkalasidan ham
    kelgan ma'lumotni ko'rsata oladi, chunki DRF `get_attribute()` avval dict-key,
    keyin object-attribute'ni sinaydi."""
    id = serializers.IntegerField()
    guest_name = serializers.CharField()
    room_type = RoomTypeShortSerializer()
    assigned_room = AssignedRoomShortSerializer(allow_null=True)
    status = serializers.ChoiceField(choices=Reservation.Status.choices)
    check_in_date = serializers.DateField()
    check_out_date = serializers.DateField()
    created_at = serializers.DateTimeField()


class ReservationWriteSerializer(serializers.ModelSerializer):
    """Create uchun — validatsiya shu yerda, orkestratsiya (inventory lock,
    overbooking tekshiruvi) `services.create_reservation`da."""

    class Meta:
        model = Reservation
        fields = ['guest_name', 'room_type', 'check_in_date', 'check_out_date']

    def validate(self, attrs):
        check_in = attrs.get('check_in_date')
        check_out = attrs.get('check_out_date')

        if check_out <= check_in:
            raise serializers.ValidationError(
                {'check_out_date': "Check-out sana check-in sanadan keyin bo'lishi kerak"}
            )
        return attrs

    def create(self, validated_data):
        return create_reservation(
            guest_name=validated_data['guest_name'],
            room_type_id=validated_data['room_type'].id,
            check_in_date=validated_data['check_in_date'],
            check_out_date=validated_data['check_out_date'],
        )

    def to_representation(self, instance):
        # response'ni Detail shaklida qaytarish — ORM instance ham dict kabi
        # to'g'ri serialize bo'ladi (DRF get_attribute() ikkalasini ham qo'llab-quvvatlaydi)
        return ReservationDetailSerializer(instance).data


class ReservationCancelSerializer(serializers.Serializer):
    """Cancel action uchun — bo'sh body, faqat orkestratsiya."""

    def save(self, **kwargs):
        reservation_id = self.context['reservation_id']
        return cancel_reservation(reservation_id)

    def to_representation(self, instance):
        return ReservationDetailSerializer(instance).data