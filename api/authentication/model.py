from flask_security import RoleMixin, UserMixin
from utils.ext import db
from functools import reduce
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime


class Permission(object):
    LOGIN = 0X01
    EDITOR = 0x02
    OPERATOR = 0x04
    ADMIN = 0xff        # hex(255)
    PERMISSION_MAP = {
        LOGIN: ('login', 'Login user'),
        EDITOR: ('editor', 'Editor'),
        OPERATOR: ('op', 'Operator'),
        ADMIN: ('admin', 'Super administrator')
    }

roles_users = db.Table(
    'roles_users',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id')))


class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True)
    permissions = db.Column(db.Integer, default=Permission.LOGIN)
    description = db.Column(db.String(255))
    groups_id = db.Column(db.Integer, db.ForeignKey('groups.id'))


class Groups(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True)
    description = db.Column(db.String(255))
    roles = db.relationship('Role', backref='groups', lazy='dynamic')


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    username = db.Column(db.String(255), unique=True)
    phone = db.Column(db.String(255))
    password_hash = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime(), default=datetime.now())
    roles = db.relationship('Role', secondary=roles_users, backref=db.backref('users', lazy='dynamic'))
    last_login_at = db.Column(db.String(255))
    current_login_at = db.Column(db.String(255))
    last_login_ip = db.Column(db.String(255))
    current_login_ip = db.Column(db.String(255))
    login_count = db.Column(db.Integer)

    # 权限验证
    def can(self, gid, permissions):
        if (self.roles is None) or (gid is None):
            print("can false")
            return False
        # 判断是否在组中 [ r for r in self.roles if 组 == r.组]
        permissions_list = [r.permissions for r in self.roles if r.groups_id == int(gid) or r.groups.name == "admin"]
        if permissions_list:
            all_perms = reduce(lambda x, y: x | y, permissions_list)
        else:
            all_perms = 0
        print("all_perms", all_perms)
        return all_perms & permissions == permissions

    def can_admin(self):
        return self.can(Permission.ADMIN)

    # password不可读
    @property
    def password(self):
        raise AttributeError('`password` is not a readable attribute')

    # password加密
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    # 验证password
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

