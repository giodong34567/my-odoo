from odoo import api, fields, models


class DemoQuery(models.Model):
    """
    Demo: Các cách truy vấn dữ liệu trong Odoo ORM + raw SQL.
    """
    _name = 'demo.query'
    _description = 'Demo Query'

    name = fields.Char(required=True)

    # ── 1. search() ───────────────────────────────────────────────
    @api.model
    def demo_search(self):
        # Tìm tất cả
        all_emp = self.env['demo.employee'].search([])

        # Domain cơ bản
        it_emp = self.env['demo.employee'].search([
            ('department', '=', 'it'),
            ('salary', '>=', 10_000_000),
        ])

        # order, limit, offset
        top3 = self.env['demo.employee'].search(
            [('active', '=', True)],
            order='salary desc',
            limit=3,
            offset=0,
        )

        # Toán tử hay dùng trong domain:
        # =, !=, <, >, <=, >=
        # 'like'  => có chứa (case-sensitive)
        # 'ilike' => có chứa (case-insensitive)  ← hay dùng nhất
        # 'in', 'not in'
        # 'child_of' => tìm theo cây (Many2one có parent)
        # '|' OR,  '&' AND (prefix notation),  '!' NOT
        result = self.env['demo.employee'].search([
            '|',
            ('department', '=', 'it'),
            ('salary', '>', 20_000_000),
        ])
        return result

    # ── 2. search_count() ─────────────────────────────────────────
    @api.model
    def demo_search_count(self):
        # Đếm không cần load record — hiệu quả hơn len(search(...))
        count = self.env['demo.employee'].search_count([
            ('department', '=', 'it')
        ])
        return count

    # ── 3. browse() ───────────────────────────────────────────────
    @api.model
    def demo_browse(self):
        # Lấy record theo id đã biết — không query DB ngay, lazy load
        emp = self.env['demo.employee'].browse(1)
        emp_multi = self.env['demo.employee'].browse([1, 2, 3])
        return emp_multi

    # ── 4. filtered(), mapped(), sorted() ────────────────────────
    @api.model
    def demo_recordset_ops(self):
        employees = self.env['demo.employee'].search([])

        # filtered: lọc recordset trong Python (không query DB thêm)
        seniors = employees.filtered(lambda e: e.total_salary > 20_000_000)

        # filtered_domain: dùng domain thay lambda (Odoo 15+)
        it_team = employees.filtered_domain([('department', '=', 'it')])

        # mapped: lấy giá trị field hoặc transform
        names = employees.mapped('name')           # => ['An', 'Bình', ...]
        totals = employees.mapped('total_salary')  # => [15000000, ...]
        # mapped qua quan hệ
        # departments = contracts.mapped('employee_id.department')

        # sorted: sắp xếp recordset trong Python
        by_salary = employees.sorted('salary', reverse=True)
        by_custom = employees.sorted(key=lambda e: e.total_salary)

        return seniors

    # ── 5. read() và read_group() ─────────────────────────────────
    @api.model
    def demo_read_group(self):
        # read(): lấy dict thay vì recordset — nhanh hơn khi chỉ cần vài field
        data = self.env['demo.employee'].search([]).read(['name', 'salary'])
        # => [{'id': 1, 'name': 'An', 'salary': 15000000}, ...]

        # read_group: GROUP BY — tổng hợp dữ liệu không cần load từng record
        result = self.env['demo.employee'].read_group(
            domain=[('active', '=', True)],
            fields=['department', 'salary:sum', 'salary:avg'],
            groupby=['department'],
        )
        # => [{'department': 'it', 'salary': 45000000, 'department_count': 3}, ...]
        return result

    # ── 6. exists() ───────────────────────────────────────────────
    @api.model
    def demo_exists(self):
        emp = self.env['demo.employee'].browse(9999)
        if not emp.exists():
            return "Record không tồn tại"
        return emp.name

    # ── 7. Raw SQL — self.env.cr ──────────────────────────────────
    @api.model
    def demo_raw_sql(self):
        """
        Dùng raw SQL khi ORM không đủ mạnh:
        - Query phức tạp (window function, CTE...)
        - Cần tối ưu performance
        - Bulk update hàng loạt

        LUÔN dùng %s placeholder, KHÔNG bao giờ format string trực tiếp
        => tránh SQL injection
        """
        cr = self.env.cr

        # SELECT
        cr.execute("""
            SELECT id, name, salary
            FROM demo_employee
            WHERE department = %s AND salary > %s
            ORDER BY salary DESC
        """, ('it', 10_000_000))
        rows = cr.fetchall()   # list of tuples
        # row = cr.fetchone()  # 1 tuple
        # rows = cr.dictfetchall()  # list of dicts ← tiện hơn

        # INSERT / UPDATE — dùng khi cần bypass ORM (không trigger compute/onchange)
        cr.execute("""
            UPDATE demo_employee
            SET allowance = %s
            WHERE department = %s
        """, (500_000, 'hr'))

        return rows
