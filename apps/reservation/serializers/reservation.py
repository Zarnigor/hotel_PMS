"""Reservation serializers — List/Detail selectordan (nested dict) keladigan
ma'lumot bilan ishlaydi, Write esa serializer validatsiyasidan keyin service'ga
yo'naltiradi (ORM, Reservation instance qaytaradi)."""

from rest_framework import serializers

from apps.reservation.models import Reservation
from apps.reservation.services import create_reservation, cancel_reservation
from apps.room.serializers import RoomTypeShortSerializer, AssignedRoomShortSerializer


class ReservationListSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    guest_name = serializers.CharField()
    room_type = RoomTypeShortSerializer()
    status = serializers.ChoiceField(choices=Reservation.Status.choices)
    check_in_date = serializers.DateField()
    check_out_date = serializers.DateField()


class ReservationDetailSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    guest_name = serializers.CharField()
    room_type_id = serializers.IntegerField()
    assigned_room = serializers.IntegerField(allow_null=True)
    status = serializers.ChoiceField(choices=Reservation.Status.choices)
    check_in_date = serializers.DateField()
    check_out_date = serializers.DateField()


class ReservationWriteSerializer(serializers.ModelSerializer):
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
        return ReservationDetailSerializer(instance, context=self._context).data


class ReservationCancelSerializer(serializers.Serializer):
    def save(self, **kwargs):
        reservation_id = self.context['reservation_id']
        return cancel_reservation(reservation_id)

    def to_representation(self, instance):
        return ReservationDetailSerializer(instance).data