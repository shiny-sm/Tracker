from django.db import models
from django. contrib. auth.models import AbstractUser
from datetime import date
# Create your models here.
class User(AbstractUser):
    empcode = models.CharField(max_length=50)
    empmobile = models.CharField(max_length=50)
    is_projectmanager = models.BooleanField(default=False)
    usertype = models.IntegerField(default=False)


class Team(models.Model):
    PMid = models.ForeignKey(User, on_delete=models.CASCADE,related_name='forPMId')
    is_active = models.BooleanField(default=False)
    members = models.ManyToManyField(User, through='TeamMembership')

    def __int__(self):
        return self.PMid

    class Meta:
        db_table = 'teams'

class TeamMembership(models.Model):
    staffid  = models.ForeignKey(User, on_delete=models.CASCADE,related_name='forstaffId')
    teamid = models.ForeignKey(Team, on_delete=models.CASCADE)

class TaskCategory(models.Model):
    category = models.CharField(max_length=50)
    forpm = models.BooleanField(default=False,null=True)

    class Meta:
        db_table = 'taskcategory'

class TaskSubCategory(models.Model):
    CatId = models.ForeignKey(TaskCategory, on_delete=models.CASCADE)
    subcategory = models.CharField(max_length=50)

    class Meta:
        db_table = 'tasksubcategory'

# class Projects(models.Model):
#     PMId = models.ForeignKey(User, on_delete=models.CASCADE)
#     project = models.CharField(max_length=50,default=False,null=True)

#     class Meta:
#         db_table = 'projects'
class Projects(models.Model):
    project = models.CharField(max_length=50,default=False,null=True)
    status = models.BooleanField(default=False)

    class Meta:
        db_table = 'projects'


class PMProjects(models.Model):
    PMId = models.ForeignKey(User, on_delete=models.CASCADE)
    projectid = models.ForeignKey(Projects, on_delete=models.CASCADE)

    class Meta:
        db_table = 'pmprojects'

class Task(models.Model):
    userid = models.ForeignKey(User, on_delete=models.CASCADE)
    PMId = models.ForeignKey(User, on_delete=models.CASCADE,related_name='manager')
    projectid = models.ForeignKey(Projects, on_delete=models.CASCADE)
    catid = models.ForeignKey(TaskCategory, on_delete=models.CASCADE)
    subcatid = models.ForeignKey(TaskSubCategory, on_delete=models.CASCADE)
    startdate = models.DateField()
    enddate = models.DateField()
    hours = models.IntegerField()
    description = models.CharField(max_length=500)
    comments  = models.CharField(max_length=500)
    work_status = models.BooleanField(default=False)

class WorkingHours(models.Model):
    monthyear = models.CharField(max_length=50)
    tothours = models.IntegerField()

    class Meta:
        db_table = 'workinghours'

