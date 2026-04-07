from odoo import fields, models


class StudentPerson(models.Model):
    """
    Model chứa thông tin cá nhân cơ bản.
    Đây là model CHA trong delegation inheritance.

    Tưởng tượng đây là "hồ sơ cá nhân" — bất kỳ ai cũng có:
    tên, ngày sinh, giới tính, email, phone...
    """
    _name = 'student.person'
    _description = 'Thông tin cá nhân'

    name   = fields.Char(string='Họ và tên', required=True)
    dob    = fields.Date(string='Ngày sinh')
    gender = fields.Selection([('male', 'Nam'), ('female', 'Nữ')], string='Giới tính')
    email  = fields.Char(string='Email')
    phone  = fields.Char(string='Số điện thoại')
    address = fields.Char(string='Địa chỉ')
    