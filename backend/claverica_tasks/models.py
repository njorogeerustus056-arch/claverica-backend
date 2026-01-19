from django.db import models

# Models will be auto-generated based on existing database tables


class TasksClavericatask(models.Model):
    """
    Model for claverica_tasks_clavericatask table
    """
    # TODO: Add fields based on actual table structure
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'claverica_tasks_clavericatask'
        verbose_name = 'TasksClavericatask'
        verbose_name_plural = 'TasksClavericatasks'


class TasksRewardwithdrawal(models.Model):
    """
    Model for claverica_tasks_rewardwithdrawal table
    """
    # TODO: Add fields based on actual table structure
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'claverica_tasks_rewardwithdrawal'
        verbose_name = 'TasksRewardwithdrawal'
        verbose_name_plural = 'TasksRewardwithdrawals'


class TasksTaskcategory(models.Model):
    """
    Model for claverica_tasks_taskcategory table
    """
    # TODO: Add fields based on actual table structure
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'claverica_tasks_taskcategory'
        verbose_name = 'TasksTaskcategory'
        verbose_name_plural = 'TasksTaskcategorys'


class TasksUserrewardbalance(models.Model):
    """
    Model for claverica_tasks_userrewardbalance table
    """
    # TODO: Add fields based on actual table structure
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'claverica_tasks_userrewardbalance'
        verbose_name = 'TasksUserrewardbalance'
        verbose_name_plural = 'TasksUserrewardbalances'
