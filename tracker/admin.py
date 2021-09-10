from django.contrib import admin

# Register your models here.
from tracker.models import User
from tracker.models import Team
from tracker.models import TeamMembership

admin.site.register(User)
admin.site.register(Team)
admin.site.register(TeamMembership)