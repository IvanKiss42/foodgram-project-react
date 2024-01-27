from django.contrib import admin

from .models import User, Subscription


class UserAdmin(admin.ModelAdmin):
    list_display = ('username',
                    'email',
                    'id',
                    'first_name',
                    'last_name',
                    'role',)
    search_fields = ('username', 'email')
    list_filter = ('username', 'email')
    list_editable = ('email', )
    empty_value_display = '-пусто-'


admin.site.register(User, UserAdmin)
admin.site.register(Subscription)
