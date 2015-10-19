from models import PlotLayout, DataSet, DataLayout, Plot1D, Plot2D
from django.contrib import admin

class Plot1DAdmin(admin.ModelAdmin):
    list_display = ('id', 'owner', 'filename')
    
class Plot2DAdmin(admin.ModelAdmin):
    list_display = ('id', 'owner', 'filename')
    
class DataSetAdmin(admin.ModelAdmin):
    list_display = ('id', 'owner', 'data')
    
class DataLayoutAdmin(admin.ModelAdmin):
    list_display = ('id', 'owner', 'color', 'size')
    
class PlotLayoutAdmin(admin.ModelAdmin):
    list_display = ('id', 'owner', 'title')
    
admin.site.register(PlotLayout, PlotLayoutAdmin)
admin.site.register(DataSet, DataSetAdmin)
admin.site.register(DataLayout, DataLayoutAdmin)
admin.site.register(Plot1D, Plot1DAdmin)
admin.site.register(Plot2D, Plot2DAdmin)
