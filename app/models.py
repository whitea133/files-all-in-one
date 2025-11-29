"""
项目:AmberDay
数据库模型文件
数据库：Sqlite
"""
from tortoise.models import Model
from tortoise import fields

class VirtualFold(Model):
    """
        虚拟文件夹
        id: 主键
        name: 虚拟文件夹名称
        description: 虚拟文件夹描述
        create_time: 创建时间
    """    
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255, unique=True)
    description = fields.TextField(null=True)
    create_time = fields.DatetimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
class FileAnchor(Model):
    """
        资料文件锚点
        id: 主键
        name: 文件锚点名称
        path: 文件路径
        description: 文件锚点描述
        create_time: 创建时间
        update_time: 更新时间
        is_valid: 是否有效
    """    
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255)
    path = fields.CharField(max_length=1024)
    description = fields.TextField(null=True)
    create_time = fields.DatetimeField(auto_now_add=True)
    update_time = fields.DatetimeField(auto_now=True)
    is_valid = fields.BooleanField(default=True)

    # 资料锚点与虚拟文件夹的多对多关系
    virtual_folders = fields.ManyToManyField('models.VirtualFold', related_name='file_anchors', through='fileanchor_virtualfold')
    # 资料锚点与标签的多对多关系
    tags = fields.ManyToManyField('models.Tag', related_name='file_anchors', through='fileanchor_tag')

    def __str__(self):
        return self.name

class Tag(Model):
    """
        资料标签
        id: 主键
        name: 标签名称
        use_count: 使用次数
        create_time: 创建时间
    """    
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=100, unique=True)
    use_count = fields.IntField(default=0)
    create_time = fields.DatetimeField(auto_now_add=True)


class BackupRecord(Model):
    """
        资料备份记录
        id: 主键
        file_anchor: 关联的资料文件锚点(外键)
        backup_path: 备份文件路径
        backup_time: 备份时间
    """    
    id = fields.IntField(pk=True)
    file_anchor = fields.ForeignKeyField('models.FileAnchor', related_name='backup_records')
    backup_path = fields.CharField(max_length=1024)
    backup_time = fields.DatetimeField(auto_now_add=True)

class OperatorLog(Model):
    """
        操作日志
        id: 主键
        operator_type: 操作类型(外键)
        result: 操作结果
        time: 操作时间
    """ 
    id = fields.IntField(pk=True)
    operator_type = fields.ForeignKeyField('models.OperatorType', related_name='operator_logs')
    result = fields.TextField()
    time = fields.DatetimeField(auto_now_add=True)

class OperatorType(Model):
    """
        操作类型
        id: 主键
        name: 操作类型名称
        description: 操作类型描述
    """ 
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=100, unique=True)
    description = fields.TextField(null=True)