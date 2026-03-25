from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class Student(models.Model):
    _name = 'student.student'
    _description = 'Học sinh'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(string='Họ và tên', required=True, tracking=True)
    student_code = fields.Char(string='Mã học sinh', readonly=True, copy=False, default='New')
    age = fields.Integer(string='Tuổi')
    gender = fields.Selection([
        ('male', 'Nam'),
        ('female', 'Nữ'),
    ], string='Giới tính')
    email = fields.Char(string='Email')
    address = fields.Char(string='Địa chỉ', default='Quảng Trị', required=True, tracking=True)
    phone = fields.Char(string='Số điện thoại')
    active = fields.Boolean(default=True)

    # ── Ví dụ default động ───────────────────────────────────────
    # Cách 1: lambda self — dùng khi logic đơn giản, 1 dòng
    enroll_date = fields.Date(
        string='Ngày nhập học',
        default=lambda self: fields.Date.today(),
    )

    # Cách 2: lambda self gọi method — dùng khi logic phức tạp hơn
    note = fields.Text(
        string='Ghi chú',
        default=lambda self: self._default_note(),
    )

    def _default_note(self):
        """
        Method trả về giá trị default động.
        self ở đây là model (không phải record cụ thể),
        nên có thể dùng self.env để truy cập user, company...
        """
        return f"Học sinh nhập học năm {fields.Date.today().year} - {self.env.company.name}"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('student_code', 'New') == 'New':
                vals['student_code'] = self.env['ir.sequence'].next_by_code('student.student') or 'New'
        return super().create(vals_list)

    @api.constrains('age')
    def _check_age(self):
        for rec in self:
            if rec.age and not (5 <= rec.age <= 100):
                raise ValidationError(_('Tuổi không hợp lệ.'))

    
    @api.constrains('name')
    def _check_age(self):
        for rec in self:
            if rec.name and not (3 <= len(rec.name) <= 50):
                raise ValidationError (_('Tên của học sinh phải từ 3 đến 50 ký tự'))
