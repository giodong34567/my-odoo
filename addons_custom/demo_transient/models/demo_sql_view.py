from odoo import fields, models


class DemoSqlView(models.Model):
    """
    Demo: _auto = False — Model ánh xạ lên SQL View, không tạo bảng DB.

    Dùng khi:
    - Cần báo cáo / dashboard tổng hợp từ nhiều bảng
    - Query phức tạp (GROUP BY, JOIN, window function...)
    - Chỉ cần đọc, không cần ghi

    Odoo gốc dùng nhiều: sale.report, account.invoice.report, stock.report...
    """
    _name = 'demo.sql.view'
    _description = 'Demo SQL View'
    _auto = False       # không tạo bảng, Odoo sẽ gọi init() để tạo VIEW
    _rec_name = 'employee_name'

    # Các field phải khớp với cột trong SQL VIEW bên dưới
    employee_name = fields.Char(string='Nhân viên', readonly=True)
    department    = fields.Selection([
        ('it', 'IT'), ('hr', 'Nhân sự'),
        ('accounting', 'Kế toán'), ('sales', 'Kinh doanh'),
    ], string='Phòng ban', readonly=True)
    total_salary  = fields.Float(string='Tổng lương', readonly=True)
    employee_count = fields.Integer(string='Số nhân viên', readonly=True)
    avg_salary    = fields.Float(string='Lương TB', readonly=True)

    def init(self):
        """
        Odoo gọi init() khi install/update module.
        Tạo hoặc thay thế SQL VIEW tại đây.
        """
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW demo_sql_view AS (
                SELECT
                    ROW_NUMBER() OVER ()        AS id,  -- bắt buộc phải có id
                    e.name                      AS employee_name,
                    e.department                AS department,
                    e.total_salary              AS total_salary,
                    COUNT(*) OVER (
                        PARTITION BY e.department
                    )                           AS employee_count,
                    AVG(e.total_salary) OVER (
                        PARTITION BY e.department
                    )                           AS avg_salary
                FROM demo_employee e
                WHERE e.active = TRUE
            )
        """)
