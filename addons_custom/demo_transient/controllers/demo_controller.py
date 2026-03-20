import json
from odoo import http
from odoo.http import request


class DemoController(http.Controller):
    """
    Demo: HTTP Controller — định nghĩa route (URL endpoint) trong Odoo.

    auth=
      'public'  => ai cũng gọi được, kể cả chưa đăng nhập
      'user'    => phải đăng nhập (default)
      'none'    => Odoo không xử lý session, tự quản lý hoàn toàn

    type=
      'http' => trả về HTML / Response thông thường
      'json' => nhận và trả về JSON (RPC style), tự wrap {result: ...}
    """

    # ── HTTP route — trả về HTML ──────────────────────────────────
    @http.route('/demo/hello', type='http', auth='public', methods=['GET'])
    def hello(self, **kwargs):
        # request.env: ORM environment của user hiện tại
        # request.env.user: user đang đăng nhập (hoặc public user)
        user_name = request.env.user.name
        return f"<h1>Xin chào, {user_name}!</h1>"

    # ── JSON route — REST-style API ───────────────────────────────
    @http.route('/demo/employees', type='json', auth='user', methods=['POST'])
    def get_employees(self, department=None, **kwargs):
        """
        type='json': Odoo tự parse body JSON, tự wrap response.
        Client gửi: POST /demo/employees  body: {"department": "it"}
        Client nhận: {"result": [...]}  hoặc  {"error": {...}}
        """
        domain = [('department', '=', department)] if department else []
        employees = request.env['demo.employee'].search(domain)

        return employees.read(['name', 'department', 'total_salary'])

    # ── Nhận dữ liệu từ form POST ─────────────────────────────────
    @http.route('/demo/create', type='http', auth='user', methods=['POST'], csrf=True)
    def create_employee(self, name, department, salary, **kwargs):
        """
        csrf=True (default): bảo vệ CSRF cho form HTML.
        Tham số từ form tự động map vào tham số method.
        """
        emp = request.env['demo.employee'].create({
            'name': name,
            'department': department,
            'salary': float(salary),
        })
        return request.redirect(f'/web#model=demo.employee&id={emp.id}')

    # ── Trả về JSON thủ công (không dùng type='json') ─────────────
    @http.route('/demo/stats', type='http', auth='user', methods=['GET'])
    def stats(self, **kwargs):
        count = request.env['demo.employee'].search_count([])
        data = {'total_employees': count, 'user': request.env.user.name}
        return request.make_response(
            json.dumps(data),
            headers=[('Content-Type', 'application/json')],
        )
