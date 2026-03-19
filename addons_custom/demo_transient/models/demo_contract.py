from odoo import fields, models


class DemoContract(models.Model):
    """
    DELEGATION INHERITANCE - _inherits

    Khác với _inherit (classical) và _name + _inherit (prototype):
    - _inherits tạo ra 2 bảng riêng biệt trong DB
    - model con có một Many2one bắt buộc trỏ đến model cha
    - các field của cha được "ủy quyền" - truy cập trực tiếp từ con
      nhưng thực ra đang đọc/ghi vào bảng cha

    Ví dụ thực tế trong Odoo gốc:
      res.users  _inherits  res.partner
      product.product  _inherits  product.template
    """
    _name = 'demo.contract'
    _description = 'Demo Contract'

    # Đây là "delegation link" - bắt buộc phải có, required=True
    # Odoo sẽ tự tạo record demo.employee khi tạo demo.contract
    _inherits = {'demo.employee': 'employee_id'}

    employee_id = fields.Many2one(
        'demo.employee',
        string='Nhân viên',
        required=True,
        ondelete='cascade',  # xóa contract => xóa employee luôn
    )

    # Field riêng của contract - chỉ có trong bảng demo_contract
    contract_date = fields.Date(string='Ngày ký hợp đồng', required=True)
    duration_months = fields.Integer(string='Thời hạn (tháng)', default=12)
    contract_type = fields.Selection([
        ('fulltime', 'Toàn thời gian'),
        ('parttime', 'Bán thời gian'),
        ('probation', 'Thử việc'),
    ], string='Loại hợp đồng', required=True, default='fulltime')
    note = fields.Text(string='Ghi chú')

    # Nhờ _inherits, các field sau đây của demo.employee
    # có thể truy cập trực tiếp trên demo.contract:
    #   contract.name        => thực ra là contract.employee_id.name
    #   contract.department  => thực ra là contract.employee_id.department
    #   contract.salary      => thực ra là contract.employee_id.salary
