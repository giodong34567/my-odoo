from odoo import _, api, fields, models
from odoo.exceptions import UserError


class DemoModelTricks(models.Model):
    """
    Demo: _sql_constraints và copy()

    _sql_constraints: ràng buộc dữ liệu ở tầng DB (nhanh hơn @api.constrains)
    copy(): kiểm soát hành vi khi duplicate record
    """
    _name = 'demo.model.tricks'
    _description = 'Demo Model Tricks'

    # ── _sql_constraints ──────────────────────────────────────────
    # Định nghĩa constraint trực tiếp ở DB (PostgreSQL CHECK / UNIQUE)
    # Ưu điểm so với @api.constrains:
    #   - Chạy ở tầng DB => nhanh hơn, đảm bảo toàn vẹn dữ liệu tuyệt đối
    #   - Không thể bypass dù dùng raw SQL
    # Nhược điểm: không viết logic Python phức tạp được
    _sql_constraints = [
        # (tên_constraint, định_nghĩa_sql, thông_báo_lỗi_hiển_thị)
        (
            'unique_code',
            'UNIQUE(code)',
            'Mã đã tồn tại, vui lòng dùng mã khác.',
        ),
        (
            'check_score_range',
            'CHECK(score >= 0 AND score <= 100)',
            'Điểm phải trong khoảng 0 đến 100.',
        ),
    ]

    name = fields.Char(string='Tên', required=True)
    code = fields.Char(string='Mã', required=True)
    score = fields.Integer(string='Điểm', default=0)
    note = fields.Text(string='Ghi chú')
    active = fields.Boolean(default=True)

    # ── copy() ────────────────────────────────────────────────────
    # Override để kiểm soát hành vi khi user bấm "Duplicate" trên UI
    # hoặc gọi record.copy() từ code
    def copy(self, default=None):
        """
        default: dict các giá trị muốn override khi duplicate.
        Các field có copy=False sẽ bị bỏ qua tự động.
        """
        self.ensure_one()
        default = dict(default or {})

        # Tự động thêm suffix "(Copy)" vào tên
        default.setdefault('name', f"{self.name} (Copy)")

        # Tự động sinh code mới để tránh vi phạm UNIQUE constraint
        default.setdefault('code', f"{self.code}-COPY")

        # note không copy theo (reset về rỗng)
        default.setdefault('note', False)

        return super().copy(default)

    # Ví dụ field với copy=False — sẽ không được copy khi duplicate
    ref_number = fields.Char(
        string='Số tham chiếu',
        copy=False,   # reset về False/rỗng khi duplicate
        readonly=True,
    )
