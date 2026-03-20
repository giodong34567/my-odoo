from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class DemoEmployee(models.Model):
    """
    Model thường - dữ liệu được lưu vĩnh viễn vào database.

    Minh họa các kỹ thuật:
    - fields các loại: Char, Float, Integer, Date, Selection, Boolean, Text
    - @api.depends  => compute field
    - @api.onchange => tự động điền khi user thay đổi giá trị
    - @api.constrains => validate dữ liệu
    - record rules + groups => phân quyền
    """
    _name = 'demo.employee'
    _description = 'Demo Employee'

    # ── Basic fields ──────────────────────────────────────────────
    name = fields.Char(string='Tên nhân viên', required=True)
    age = fields.Integer(string='Tuổi')
    gender = fields.Selection([
        ('male', 'Nam'),
        ('female', 'Nữ'),
        ('other', 'Khác'),
    ], string='Giới tính')
    phone = fields.Char(string='Số điện thoại')
    email = fields.Char(string='Email')
    bio = fields.Text(string='Giới thiệu bản thân')
    active = fields.Boolean(default=True)

    join_date = fields.Date(
        string='Ngày vào làm',
        default=fields.Date.today,
    )

    department = fields.Selection([
        ('it', 'IT'),
        ('hr', 'Nhân sự'),
        ('accounting', 'Kế toán'),
        ('sales', 'Kinh doanh'),
    ], string='Phòng ban', required=True)

    # Liên kết với res.users để dùng trong record rules
    user_id = fields.Many2one(
        'res.users',
        string='Tài khoản người dùng',
        ondelete='set null',
        help='Liên kết với user để áp dụng record rule phân quyền',
    )

    # Lương cơ bản + phụ cấp => tổng lương được compute
    salary = fields.Float(string='Lương cơ bản (VNĐ)', required=True)
    allowance = fields.Float(string='Phụ cấp (VNĐ)', default=0.0)

    # ── Compute fields ────────────────────────────────────────────
    total_salary = fields.Float(
        string='Tổng lương (VNĐ)',
        compute='_compute_total_salary',
        store=True,
        help='Lương cơ bản + Phụ cấp',
    )

    salary_level = fields.Selection([
        ('junior', 'Junior (< 10tr)'),
        ('mid', 'Mid (10 - 20tr)'),
        ('senior', 'Senior (> 20tr)'),
    ], string='Cấp bậc lương',
        compute='_compute_salary_level',
        store=True,
    )

    years_of_service = fields.Integer(
        string='Số năm công tác',
        compute='_compute_years_of_service',
        store=False,
    )

    # ── @api.depends ──────────────────────────────────────────────
    @api.depends('salary', 'allowance')
    def _compute_total_salary(self):
        for rec in self:
            rec.total_salary = rec.salary + rec.allowance

    @api.depends('total_salary')
    def _compute_salary_level(self):
        for rec in self:
            if rec.total_salary < 10_000_000:
                rec.salary_level = 'junior'
            elif rec.total_salary <= 20_000_000:
                rec.salary_level = 'mid'
            else:
                rec.salary_level = 'senior'

    @api.depends('join_date')
    def _compute_years_of_service(self):
        today = fields.Date.today()
        for rec in self:
            if rec.join_date:
                rec.years_of_service = (today - rec.join_date).days // 365
            else:
                rec.years_of_service = 0

    # ── @api.onchange ─────────────────────────────────────────────
    @api.onchange('department')
    def _onchange_department(self):
        """Gợi ý mức phụ cấp mặc định theo phòng ban"""
        defaults = {
            'it': 2_000_000,
            'sales': 3_000_000,
            'accounting': 1_500_000,
            'hr': 1_000_000,
        }
        if self.department:
            self.allowance = defaults.get(self.department, 0.0)

    # ── @api.constrains ───────────────────────────────────────────
    @api.constrains('age')
    def _check_age(self):
        for rec in self:
            if rec.age and not (18 <= rec.age <= 65):
                raise ValidationError(_('Tuổi nhân viên phải từ 18 đến 65.'))

    @api.constrains('salary')
    def _check_salary(self):
        for rec in self:
            if rec.salary < 0:
                raise ValidationError(_('Lương cơ bản không được âm.'))

    @api.constrains('email')
    def _check_email(self):
        for rec in self:
            if rec.email and '@' not in rec.email:
                raise ValidationError(_('Email không hợp lệ.'))


class ResUsersDemoExtension(models.Model):
    """
    Mở rộng res.users để thêm field demo_department.
    Record rule của Trưởng phòng dùng user.demo_department
    để lọc nhân viên cùng phòng ban.
    """
    _inherit = 'res.users'

    demo_department = fields.Selection([
        ('it', 'IT'),
        ('hr', 'Nhân sự'),
        ('accounting', 'Kế toán'),
        ('sales', 'Kinh doanh'),
    ], string='Phòng ban (Demo)', help='Dùng cho phân quyền demo_transient')


    # ── Basic fields ──────────────────────────────────────────────
    name = fields.Char(string='Tên nhân viên', required=True)
    age = fields.Integer(string='Tuổi')
    gender = fields.Selection([
        ('male', 'Nam'),
        ('female', 'Nữ'),
        ('other', 'Khác'),
    ], string='Giới tính')
    phone = fields.Char(string='Số điện thoại')
    email = fields.Char(string='Email')
    bio = fields.Text(string='Giới thiệu bản thân')
    active = fields.Boolean(default=True)

    join_date = fields.Date(
        string='Ngày vào làm',
        default=fields.Date.today,
    )

    department = fields.Selection([
        ('it', 'IT'),
        ('hr', 'Nhân sự'),
        ('accounting', 'Kế toán'),
        ('sales', 'Kinh doanh'),
    ], string='Phòng ban', required=True)

    # Lương cơ bản + phụ cấp => tổng lương được compute
    salary = fields.Float(string='Lương cơ bản (VNĐ)', required=True)
    allowance = fields.Float(string='Phụ cấp (VNĐ)', default=0.0)

    # ── Compute fields ────────────────────────────────────────────
    total_salary = fields.Float(
        string='Tổng lương (VNĐ)',
        compute='_compute_total_salary',
        store=True,
        # store=True => lưu vào DB, tái tính khi salary/allowance thay đổi
        help='Lương cơ bản + Phụ cấp',
    )

    salary_level = fields.Selection([
        ('junior', 'Junior (< 10tr)'),
        ('mid', 'Mid (10 - 20tr)'),
        ('senior', 'Senior (> 20tr)'),
    ], string='Cấp bậc lương',
        compute='_compute_salary_level',
        store=True,
    )

    years_of_service = fields.Integer(
        string='Số năm công tác',
        compute='_compute_years_of_service',
        store=False,
        # store=False => tính lại mỗi lần đọc, không lưu DB
    )

    # ── @api.depends ──────────────────────────────────────────────
    @api.depends('salary', 'allowance')
    def _compute_total_salary(self):
        """Tổng lương = lương cơ bản + phụ cấp"""
        for rec in self:
            rec.total_salary = rec.salary + rec.allowance

    @api.depends('total_salary')
    def _compute_salary_level(self):
        """Phân loại cấp bậc dựa trên tổng lương"""
        for rec in self:
            if rec.total_salary < 10_000_000:
                rec.salary_level = 'junior'
            elif rec.total_salary <= 20_000_000:
                rec.salary_level = 'mid'
            else:
                rec.salary_level = 'senior'

    @api.depends('join_date')
    def _compute_years_of_service(self):
        """Số năm công tác tính từ ngày vào làm đến hôm nay"""
        today = fields.Date.today()
        for rec in self:
            if rec.join_date:
                delta = today - rec.join_date
                rec.years_of_service = delta.days // 365
            else:
                rec.years_of_service = 0

    # ── @api.onchange ─────────────────────────────────────────────
    @api.onchange('department')
    def _onchange_department(self):
        """Gợi ý mức phụ cấp mặc định theo phòng ban"""
        defaults = {
            'it': 2_000_000,
            'sales': 3_000_000,
            'accounting': 1_500_000,
            'hr': 1_000_000,
        }
        if self.department:
            self.allowance = defaults.get(self.department, 0.0)

    # ── @api.constrains ───────────────────────────────────────────
    @api.constrains('age')
    def _check_age(self):
        for rec in self:
            if rec.age and not (18 <= rec.age <= 65):
                raise ValidationError(_('Tuổi nhân viên phải từ 18 đến 65.'))

    @api.constrains('salary')
    def _check_salary(self):
        for rec in self:
            if rec.salary < 0:
                raise ValidationError(_('Lương cơ bản không được âm.'))

    @api.constrains('email')
    def _check_email(self):
        for rec in self:
            if rec.email and '@' not in rec.email:
                raise ValidationError(_('Email không hợp lệ.'))
