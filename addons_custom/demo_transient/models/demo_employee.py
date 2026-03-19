from odoo import fields, models


class DemoEmployee(models.Model):
    """
    Model thường - dữ liệu được lưu vĩnh viễn vào database.
    Đây là model nhân viên đơn giản để minh họa.
    """
    _name = 'demo.employee'
    _description = 'Demo Employee'

    name = fields.Char(string='Tên nhân viên', required=True)
    department = fields.Selection([
        ('it', 'IT'),
        ('hr', 'Nhân sự'),
        ('accounting', 'Kế toán'),
        ('sales', 'Kinh doanh'),
    ], string='Phòng ban', required=True)
    salary = fields.Float(string='Lương (VNĐ)', required=True)
    active = fields.Boolean(default=True)
