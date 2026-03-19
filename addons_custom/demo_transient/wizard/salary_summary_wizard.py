from odoo import api, fields, models


class SalarySummaryWizard(models.TransientModel):
    """
    TRANSIENT MODEL - Wizard tính tổng lương theo phòng ban.

    Điểm khác biệt với models.Model thường:
    1. Kế thừa models.TransientModel thay vì models.Model
    2. Dữ liệu chỉ tồn tại tạm thời - Odoo tự xóa sau ~1 giờ (ir.autovacuum)
    3. Không nên dùng để lưu dữ liệu quan trọng lâu dài
    4. Thường dùng cho: wizard nhập liệu, báo cáo tạm, xác nhận hành động hàng loạt
    """
    _name = 'salary.summary.wizard'
    _description = 'Wizard Tổng Hợp Lương'
    _transient_max_hours = 1/60  # tự xóa sau 1 phút (để test)

    # --- BƯỚC 1: Người dùng nhập điều kiện lọc ---

    department = fields.Selection([
        ('all', 'Tất cả phòng ban'),
        ('it', 'IT'),
        ('hr', 'Nhân sự'),
        ('accounting', 'Kế toán'),
        ('sales', 'Kinh doanh'),
    ], string='Phòng ban', required=True, default='all')

    min_salary = fields.Float(string='Lương tối thiểu', default=0)

    # --- BƯỚC 2: Kết quả sau khi tính toán ---
    # Các field này được điền sau khi bấm "Tính toán"

    employee_count = fields.Integer(string='Số nhân viên', readonly=True)
    total_salary = fields.Float(string='Tổng lương', readonly=True)
    average_salary = fields.Float(string='Lương trung bình', readonly=True)
    result_note = fields.Text(string='Kết quả', readonly=True)

    # Trạng thái wizard: 'input' = đang nhập, 'result' = đã có kết quả
    state = fields.Selection([
        ('input', 'Nhập điều kiện'),
        ('result', 'Xem kết quả'),
    ], default='input')

    def action_compute(self):
        """
        Tính toán và cập nhật kết quả vào chính record transient này.
        Vì là TransientModel, record này vẫn còn trong session hiện tại.
        """
        self.ensure_one()

        # Xây dựng domain lọc nhân viên
        domain = [('salary', '>=', self.min_salary)]
        if self.department != 'all':
            domain.append(('department', '=', self.department))

        employees = self.env['demo.employee'].search(domain)

        total = sum(employees.mapped('salary'))
        count = len(employees)
        average = total / count if count else 0

        dept_label = dict(self._fields['department'].selection).get(self.department, '')
        note = (
            f"Phòng ban: {dept_label}\n"
            f"Lương tối thiểu lọc: {self.min_salary:,.0f} VNĐ\n"
            f"─────────────────────\n"
            f"Số nhân viên: {count}\n"
            f"Tổng lương:   {total:,.0f} VNĐ\n"
            f"Lương TB:     {average:,.0f} VNĐ"
        )

        # Ghi kết quả vào record transient hiện tại
        self.write({
            'employee_count': count,
            'total_salary': total,
            'average_salary': average,
            'result_note': note,
            'state': 'result',
        })

        # Trả về action để reload lại chính wizard này (giữ nguyên cửa sổ)
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',  # 'new' = mở dạng popup/dialog
        }

    def action_reset(self):
        """Quay lại bước nhập điều kiện."""
        self.write({'state': 'input', 'result_note': False})
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
