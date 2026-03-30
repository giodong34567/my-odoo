from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class Student(models.Model):
    _name = 'student.student'
    _description = 'Học sinh'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    # ── Fields ────────────────────────────────────────────────────
    student_code = fields.Char(string='Mã học sinh', readonly=True, copy=False, default='New')
    name         = fields.Char(string='Họ và tên', required=True, tracking=True)
    dob          = fields.Date(string='Ngày sinh')
    gender       = fields.Selection([('male', 'Nam'), ('female', 'Nữ')], string='Giới tính')
    email        = fields.Char(string='Email')
    phone        = fields.Char(string='Số điện thoại')
    address      = fields.Char(string='Địa chỉ', default='Quảng Trị')
    age          = fields.Integer(string='Tuổi')
    active       = fields.Boolean(default=True)

    enroll_date = fields.Date(
        string='Ngày nhập học',
        default=lambda self: fields.Date.today(),
    )
    note = fields.Text(
        string='Ghi chú',
        default=lambda self: self._default_note(),
    )

    def _default_note(self):
        return f"Học sinh nhập học năm {fields.Date.today().year} - {self.env.company.name}"

    # ── CRUD ──────────────────────────────────────────────────────
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('student_code', 'New') == 'New':
                vals['student_code'] = self.env['ir.sequence'].next_by_code('student.student') or 'New'
        return super().create(vals_list)

    # ── Constrains ────────────────────────────────────────────────
    @api.constrains('age')
    def _check_age(self):
        for rec in self:
            if rec.age and not (5 <= rec.age <= 100):
                raise ValidationError(_('Tuổi không hợp lệ.'))

    @api.constrains('name')
    def _check_name(self):
        for rec in self:
            if rec.name and not (3 <= len(rec.name) <= 50):
                raise ValidationError(_('Tên của học sinh phải từ 3 đến 50 ký tự'))

    # ── Window Actions ────────────────────────────────────────────
    def action_open_form(self):
        """Mở form của chính record này — target='current'"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Chi tiết học sinh',
            'res_model': 'student.student',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'current',
        }

    def action_open_in_popup(self):
        """Mở form trong popup dialog — target='new'"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Xem học sinh (Popup)',
            'res_model': 'student.student',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }

    def action_open_list_same_class(self):
        """Mở list với domain filter — cùng năm nhập học"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Học sinh nhập học năm {self.enroll_date.year if self.enroll_date else "?"}',
            'res_model': 'student.student',
            'view_mode': 'list,form',
            'domain': [('enroll_date', '>=', f'{self.enroll_date.year}-01-01'),
                       ('enroll_date', '<=', f'{self.enroll_date.year}-12-31')]
                      if self.enroll_date else [],
            'context': {'default_enroll_date': self.enroll_date},
            'target': 'current',
        }

    def action_open_new_student(self):
        """Mở form tạo mới, pre-fill qua context"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Thêm học sinh mới',
            'res_model': 'student.student',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_enroll_date': fields.Date.today(),
                'default_address': 'Quảng Trị',
                'default_phone': '123456789',
            },
        }

    # ── URL Actions ───────────────────────────────────────────────
    def action_open_odoo_docs(self):
        """Mở URL ngoài — mở tab mới trên trình duyệt"""
        return {
            'type': 'ir.actions.act_url',
            'url': 'https://www.odoo.com/documentation/18.0',
            'target': 'new', 
        }         

    def action_open_student_url(self):
        """Mở URL nội bộ — điều hướng đến record này trong Odoo"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': f'/odoo/student/{self.id}',
            'target': 'self',
        }

    # ── Server Actions ────────────────────────────────────────────
    def action_mark_as_senior(self):
        """
        Được gọi từ server action XML (records.action_mark_as_senior()).
        self là recordset các record đang được chọn trong list view.
        """
        for rec in self:
            if rec.age and rec.age >= 18:
                rec.note = f"[Lớn tuổi] {rec.note or ''}"
