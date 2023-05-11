from django import forms

class GoogleMapsSearchForm(forms.Form):
    query = forms.CharField(label="Enter search query / keywords")
    lat = forms.FloatField(label="Enter Latitude")
    lng = forms.FloatField(label="Enter Longitude")
    radius = forms.IntegerField(label="Provide me a radius from location center (in meters)")
