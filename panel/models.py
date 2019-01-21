from django.db import models

# Create your models here.


class SroTradePlace(models.Model):
    pass


class TradePlace(models.Model):
    name = models.CharField(max_length=200)
    site_url = models.CharField(max_length=100)
    sro_trade_place = models.ForeignKey(SroTradePlace)
    sro_trade_place_entry_date = models.DateField()
    sro_trade_place_elimination_date = models.DateField(null=True)


class Debtor(models.Model):
    name = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)
    patronymic = models.CharField(max_length=100)
    birth_date = models.DateField()
    birth_place = models.CharField(max_length=200)
    telephone_number = models.CharField(max_length=30, null=True)
    bankruptcy_region = models.CharField(max_length=100)
    tin = models.IntegerField()  # ИНН
    ogrnip = models.IntegerField(null=True)
    snils = models.CharField()
    category = models.CharField()
    location = models.CharField(max_length=200)
    notes = models.TextField(null=True)


class Bidding(models.Model):
    number = models.CharField()
    bidding_date = models.DateTimeField()
    placement_date = models.DateTimeField()
    trade_place = models.ForeignKey(TradePlace)
    debtor = models.ForeignKey(Debtor)
    bidding_type = models.CharField()
    offer_form = models.CharField()
    status = models.CharField()
