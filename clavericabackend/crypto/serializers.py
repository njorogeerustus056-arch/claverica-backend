from rest_framework import serializers
from .models import CryptoWallet, CryptoCurrency, CryptoTransaction, CryptoAddress

class CryptoWalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = CryptoWallet
        fields = '__all__'

class CryptoCurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = CryptoCurrency
        fields = '__all__'

class CryptoTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CryptoTransaction
        fields = '__all__'

class CryptoAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = CryptoAddress
        fields = '__all__'
