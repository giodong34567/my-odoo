# Odoo ORM - Tổng hợp kiến thức học tập

Module `demo_transient` minh họa các kỹ thuật quan trọng trong Odoo development.

---

## 1. Các loại Model

| Loại | Kế thừa | Lưu DB | Dùng khi |
|------|---------|--------|----------|
| Model thường | `models.Model` | Vĩnh viễn | Dữ liệu nghiệp vụ |
| Transient Model | `models.TransientModel` | Tạm thời (~1h) | Wizard, form nhập liệu tạm |
| Abstract Model | `models.AbstractModel` | Không | Mixin dùng chung |

```python
# Transient tự xóa sau N giờ
_transient_max_hours = 1/60  # 1 phút, để test
```

---

## 2. Ba kiểu Inheritance

### Classical (`_inherit`)
Mở rộng model có sẵn, **cùng bảng DB**.
```python
class ResUsers(models.Model):
    _inherit = 'res.users'
    demo_department = fields.Selection(...)  # thêm cột vào bảng res_users
```

### Prototype (`_name` + `_inherit`)
Copy toàn bộ fields/methods sang model mới, **bảng DB riêng**.
```python
class DemoSpecialEmployee(models.Model):
    _name = 'demo.special.employee'
    _inherit = 'demo.employee'   # copy tất cả từ demo.employee
    extra_field = fields.Char()  # thêm field riêng
```

### Delegation (`_inherits`)
Model con **ủy quyền** fields cho model cha qua Many2one, **2 bảng DB riêng**.
```python
class DemoContract(models.Model):
    _name = 'demo.contract'
    _inherits = {'demo.employee': 'employee_id'}  # delegate sang demo.employee

    # Phải khai báo tường minh trong Odoo 18
    employee_id = fields.Many2one('demo.employee', ondelete='cascade')

    # Giờ contract.name, contract.salary... đều truy cập được
    # nhưng thực ra đang đọc/ghi vào bảng demo_employee
```

**Ví dụ thực tế trong Odoo gốc:**
- `res.users` `_inherits` `res.partner`
- `product.product` `_inherits` `product.template`

---

## 3. Compute Fields

```python
# store=True  => lưu vào DB, tái tính khi dependency thay đổi
# store=False => tính lại mỗi lần đọc (default)

total_salary = fields.Float(compute='_compute_total_salary', store=True)

@api.depends('salary', 'allowance')   # khai báo dependency
def _compute_total_salary(self):
    for rec in self:                   # luôn loop, kể cả 1 record
        rec.total_salary = rec.salary + rec.allowance
```

**Lưu ý:** `@api.depends` có thể chain qua quan hệ:
```python
@api.depends('line_ids.price_unit', 'line_ids.quantity')
def _compute_total(self): ...
```

---

## 4. Onchange

```python
@api.onchange('department')
def _onchange_department(self):
    # Chỉ chạy trên UI, KHÔNG chạy khi ghi trực tiếp qua code
    # self ở đây là pseudo-record (chưa có id nếu đang tạo mới)
    self.allowance = 2_000_000
```

> Khác biệt quan trọng: `onchange` chỉ chạy trên browser, không chạy khi `create()`/`write()` từ code. Nếu cần cả hai, dùng `@api.depends` + compute, hoặc override `create`/`write`.

---

## 5. Constrains

```python
@api.constrains('age', 'salary')   # trigger khi các field này thay đổi
def _check_data(self):
    for rec in self:
        if rec.age < 18:
            raise ValidationError(_('Tuổi phải >= 18'))
```

> Khác `@api.onchange`: constrains chạy cả khi ghi từ code, onchange chỉ chạy trên UI.

---

## 6. sudo(), with_user(), with_context()

### `sudo()`
Bỏ qua **tất cả** ACL và record rules. Chạy với quyền superuser.
```python
# Dùng khi cần tạo record hệ thống mà user thường không có quyền
self.env['demo.employee'].sudo().search([])  # thấy tất cả
```
⚠️ Không lạm dụng — dễ tạo lỗ hổng bảo mật.

### `with_user(user)`
Chạy với quyền của **user cụ thể**, vẫn bị record rules.
```python
self.env['demo.employee'].with_user(some_user).search([])
self.env['demo.employee'].with_user(1).search([])  # uid=1 = admin
```

### `with_context(**ctx)`
Truyền thêm thông tin vào môi trường, không thay đổi quyền.
```python
self.with_context(no_recompute=True, lang='vi_VN').create({...})

# Đọc context trong method
lang = self.env.context.get('lang', 'en_US')
```

**Các context key hay dùng:**
| Key | Tác dụng |
|-----|----------|
| `lang` | Ngôn ngữ hiển thị |
| `active_id` | ID record đang active |
| `default_field` | Giá trị mặc định khi tạo record |
| `no_recompute` | Bỏ qua recompute (import hàng loạt) |
| `mail_notrack` | Không ghi log chatter |

---

## 7. @api.model vs @api.model_create_multi

```python
@api.model
def some_utility(self):
    # self = model class, không phải recordset
    # Dùng cho method không cần record cụ thể
    return self.env.user.name

@api.model_create_multi
def create(self, vals_list):
    # Chuẩn Odoo 16+ để override create
    # vals_list là list of dict
    for vals in vals_list:
        vals['created_by'] = self.env.user.name
    return super().create(vals_list)
```

---

## 8. Phân quyền (Groups + Record Rules)

### Groups (ACL - Access Control List)
Kiểm soát quyền **CRUD** trên toàn bộ model.

```xml
<!-- Định nghĩa group -->
<record id="group_demo_admin" model="res.groups">
    <field name="name">Quản lý</field>
    <field name="implied_ids" eval="[(4, ref('group_demo_manager'))]"/>
</record>
```

```csv
# ir.model.access.csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_employee_admin,employee.admin,model_demo_employee,demo_transient.group_demo_admin,1,1,1,1
```

### Record Rules
Lọc **record cụ thể** mà user được phép thấy (row-level security).

```xml
<record id="rule_own_records" model="ir.rule">
    <field name="model_id" ref="model_demo_employee"/>
    <field name="groups" eval="[(4, ref('group_demo_employee'))]"/>
    <!-- user.id, user.demo_department... là biến có sẵn trong domain -->
    <field name="domain_force">[('user_id', '=', user.id)]</field>
</record>
```

**Cơ chế OR/AND:**
- Nhiều rules **cùng group** → OR (thỏa 1 là được)
- Rules của **group khác nhau** → AND (phải thỏa tất cả)
- Group có rule `(1=1)` → thấy tất cả (override hết)

---

## 9. env.ref() — Lấy record theo XML ID

```python
# Lấy group
admin_group = self.env.ref('base.group_system')

# Lấy record tùy chỉnh, không raise lỗi nếu không tìm thấy
my_group = self.env.ref('demo_transient.group_demo_admin', raise_if_not_found=False)

# Lấy action, menu...
action = self.env.ref('demo_transient.action_demo_employee')
```

---

## 10. TransientModel (Wizard)

```python
class MyWizard(models.TransientModel):
    _name = 'my.wizard'
    _transient_max_hours = 1  # tự xóa sau 1 giờ

    def action_confirm(self):
        # Xử lý logic...
        # Trả về action để reload wizard hoặc đóng popup
        return {'type': 'ir.actions.act_window_close'}
```

**Mở wizard từ button:**
```python
def open_wizard(self):
    return {
        'type': 'ir.actions.act_window',
        'res_model': 'my.wizard',
        'view_mode': 'form',
        'target': 'new',  # 'new' = popup dialog
        'context': {'default_proposal_id': self.id},
    }
```

---

## Sơ đồ tổng quan module

```
demo_transient/
├── models/
│   ├── demo_employee.py       # Model thường + compute/onchange/constrains
│   ├── demo_contract.py       # Delegation inheritance (_inherits)
│   └── demo_sudo_context.py   # sudo(), with_context(), @api.model
├── wizard/
│   └── salary_summary_wizard.py  # TransientModel
├── security/
│   ├── demo_groups.xml        # Groups + Record Rules
│   └── ir.model.access.csv    # ACL theo group
└── views/
    ├── demo_employee_views.xml
    ├── demo_contract_views.xml
    └── salary_summary_wizard_views.xml
```

---

## 11. Truy vấn dữ liệu (ORM + Raw SQL)

### search() — truy vấn cơ bản
```python
# Tất cả
self.env['demo.employee'].search([])

# Có domain + options
self.env['demo.employee'].search(
    [('department', '=', 'it'), ('salary', '>=', 10_000_000)],
    order='salary desc', limit=10, offset=0,
)
```

**Toán tử domain hay dùng:**
| Toán tử | Ý nghĩa |
|---------|---------|
| `=`, `!=`, `<`, `>` | So sánh thông thường |
| `ilike` | Chứa chuỗi, không phân biệt hoa thường |
| `in`, `not in` | Trong danh sách |
| `child_of` | Tìm theo cây (parent) |
| `\|` / `&` / `!` | OR / AND / NOT (prefix) |

```python
# OR: tìm IT hoặc lương > 20tr
['\|', ('department', '=', 'it'), ('salary', '>', 20_000_000)]
```

### search_count() — đếm không load record
```python
# Hiệu quả hơn len(search(...))
count = self.env['demo.employee'].search_count([('department', '=', 'it')])
```

### browse() — lấy record theo id
```python
emp = self.env['demo.employee'].browse(1)       # lazy load, không query ngay
emps = self.env['demo.employee'].browse([1, 2]) # nhiều record
```

### filtered / mapped / sorted — thao tác trên recordset
```python
employees = self.env['demo.employee'].search([])

# filtered: lọc trong Python
seniors = employees.filtered(lambda e: e.total_salary > 20_000_000)
it_team = employees.filtered_domain([('department', '=', 'it')])  # Odoo 15+

# mapped: lấy giá trị field
names  = employees.mapped('name')           # => ['An', 'Bình']
totals = employees.mapped('total_salary')   # => [15000000, ...]

# sorted: sắp xếp trong Python
top = employees.sorted('salary', reverse=True)
```

### read_group() — GROUP BY
```python
# Tổng hợp không cần load từng record
result = self.env['demo.employee'].read_group(
    domain=[],
    fields=['department', 'salary:sum', 'salary:avg'],
    groupby=['department'],
)
# => [{'department': 'it', 'salary': 45_000_000, 'department_count': 3}, ...]
```

### read() — lấy dict thay vì recordset
```python
# Nhanh hơn khi chỉ cần vài field, không cần full record object
data = self.env['demo.employee'].search([]).read(['name', 'salary'])
# => [{'id': 1, 'name': 'An', 'salary': 15000000}, ...]
```

### exists() — kiểm tra record còn tồn tại không
```python
emp = self.env['demo.employee'].browse(9999)
if not emp.exists():
    return "Không tồn tại"
```

### Raw SQL — self.env.cr
Dùng khi ORM không đủ (window function, CTE, bulk update...).

```python
cr = self.env.cr

# SELECT
cr.execute("""
    SELECT id, name, salary FROM demo_employee
    WHERE department = %s AND salary > %s
""", ('it', 10_000_000))

rows = cr.fetchall()      # list of tuples
rows = cr.dictfetchall()  # list of dicts ← tiện hơn

# UPDATE bulk — bypass ORM, không trigger compute/onchange
cr.execute("UPDATE demo_employee SET allowance = %s WHERE department = %s",
           (500_000, 'hr'))
```

> ⚠️ Luôn dùng `%s` placeholder, **không bao giờ** f-string/format trực tiếp vào SQL — tránh SQL injection.

---

## 12. _sql_constraints — Ràng buộc tầng DB

Nhanh hơn `@api.constrains` vì chạy thẳng ở PostgreSQL, không thể bypass.

```python
_sql_constraints = [
    # (tên, định_nghĩa_sql, thông_báo_lỗi)
    ('unique_code',      'UNIQUE(code)',                    'Mã đã tồn tại.'),
    ('check_score',      'CHECK(score >= 0 AND score <= 100)', 'Điểm phải 0-100.'),
    ('unique_name_dept', 'UNIQUE(name, department)',        'Tên trùng trong phòng ban.'),
]
```

| | `_sql_constraints` | `@api.constrains` |
|--|--|--|
| Tầng | DB (PostgreSQL) | Python |
| Tốc độ | Nhanh hơn | Chậm hơn |
| Logic phức tạp | Không | Có |
| Bypass được không | Không | Có (raw SQL) |

---

## 13. copy() — Kiểm soát Duplicate

Mặc định Odoo copy tất cả field trừ những field có `copy=False`.

```python
# Field không được copy khi duplicate
ref_number = fields.Char(copy=False)  # reset về rỗng
state = fields.Selection(..., copy=False)

# Override copy() để tùy chỉnh
def copy(self, default=None):
    default = dict(default or {})
    default.setdefault('name', f"{self.name} (Copy)")  # đổi tên
    default.setdefault('code', f"{self.code}-COPY")    # sinh code mới
    default.setdefault('note', False)                  # xóa ghi chú
    return super().copy(default)
```

---

## 14. _rec_name & display_name

Mặc định Odoo dùng field `name` làm label hiển thị ở Many2one, breadcrumb...

```python
# Đổi sang field khác
_rec_name = 'code'

# Hoặc label phức tạp nhiều field => override display_name (Odoo 17+)
display_name = fields.Char(compute='_compute_display_name', store=False)

@api.depends('code', 'first_name', 'last_name')
def _compute_display_name(self):
    for rec in self:
        rec.display_name = f"{rec.code} - {rec.first_name} {rec.last_name}"
```

> Odoo 16 trở về trước dùng `name_get()`, từ 17+ chuyển sang compute `display_name`.

---

## 15. Override create() / write()

```python
@api.model_create_multi
def create(self, vals_list):
    for vals in vals_list:
        # 1. Xử lý vals trước khi tạo
        if not vals.get('code'):
            vals['code'] = self.env['ir.sequence'].next_by_code('my.model')
    
    records = super().create(vals_list)  # luôn gọi super()
    
    # 2. Post-processing sau khi tạo
    for rec in records:
        rec._do_something()
    
    return records  # luôn return kết quả super()


def write(self, vals):
    # 1. Kiểm tra / chặn trước khi ghi
    if 'state' in vals:
        locked = self.filtered(lambda r: r.state == 'done')
        if locked:
            raise ValidationError(_('Không thể sửa record đã hoàn thành'))
    
    result = super().write(vals)  # luôn gọi super()
    
    # 2. Post-processing
    if 'state' in vals:
        self._on_state_changed()
    
    return result  # luôn return kết quả super()
```

**Lưu ý quan trọng:**
- `create` nhận `vals_list` (list of dict) từ Odoo 16+, không phải dict đơn
- Luôn `return super()` — không return sẽ trả về `None`, gây lỗi khó debug
- `write` nhận 1 `vals` dict cho toàn bộ recordset, không loop vals

---

## 16. ir.sequence — Tự sinh mã

Định nghĩa sequence trong XML:
```xml
<record id="seq_my_model" model="ir.sequence">
    <field name="name">My Model Sequence</field>
    <field name="code">my.model</field>
    <field name="prefix">ORD/%(year)s/%(month)s/</field>
    <field name="padding">4</field>
    <!-- => ORD/2026/03/0001, ORD/2026/03/0002, ... -->
</record>
```

Dùng trong `create()`:
```python
@api.model_create_multi
def create(self, vals_list):
    for vals in vals_list:
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('my.model') or 'New'
    return super().create(vals_list)
```

**Prefix variables:** `%(year)s`, `%(month)s`, `%(day)s`, `%(y)s` (2 chữ số năm)

---

## 17. mail.thread — Chatter & Tracking

```python
class MyModel(models.Model):
    _inherit = ['mail.thread', 'mail.activity.mixin']

    state  = fields.Selection([...], tracking=True)  # tự log khi thay đổi
    amount = fields.Float(tracking=True)
```

Ghi log thủ công vào chatter:
```python
# Internal note (chỉ nội bộ thấy)
self.message_post(
    body='Đã xử lý xong',
    subtype_xmlid='mail.mt_note',
)

# Comment (notify followers)
self.message_post(
    body='Hoàn thành đơn hàng',
    subtype_xmlid='mail.mt_comment',
)
```

| | `mt_note` | `mt_comment` |
|--|--|--|
| Hiển thị | Chatter | Chatter |
| Notify followers | Không | Có |
| Dùng khi | Log nội bộ | Thông báo ra ngoài |

---

## 18. _order & _parent_store

### _order — sắp xếp mặc định
```python
_order = 'sequence, name'        # tăng dần
_order = 'create_date desc, id'  # giảm dần
```
Áp dụng cho mọi `search()` mà không cần truyền `order=` mỗi lần.

### _parent_store — cấu trúc cây
```python
_parent_store = True  # bật nested set, query cây cực nhanh

parent_id   = fields.Many2one('demo.hierarchy', ondelete='restrict')
parent_path = fields.Char(index=True)  # Odoo tự quản lý, không sửa tay
child_ids   = fields.One2many('demo.hierarchy', 'parent_id')
```

Tìm toàn bộ cây con bằng `child_of`:
```python
# Lấy node + tất cả con cháu của node id=5
self.env['demo.hierarchy'].search([('parent_id', 'child_of', 5)])
```

> Ví dụ thực tế: `product.category`, `account.account`, `hr.department`

---

## 19. ir.cron — Tác vụ tự động (Scheduled Actions)

Định nghĩa trong XML:
```xml
<record id="ir_cron_demo" model="ir.cron">
    <field name="name">Demo: Cập nhật thống kê</field>
    <field name="model_id" ref="model_demo_cron"/>
    <field name="state">code</field>
    <field name="code">model.action_cron_job()</field>
    <field name="interval_number">1</field>
    <field name="interval_type">days</field>  <!-- minutes/hours/days/weeks/months -->
    <field name="numbercall">-1</field>        <!-- -1 = chạy mãi mãi -->
    <field name="active">True</field>
</record>
```

Method trong Python:
```python
def action_cron_job(self):
    # Cron chạy với user __system__, nên sudo() nếu cần
    records = self.sudo().search([])
    # xử lý...
    _logger.info("Cron chạy xong: %d records", len(records))
```

> Xem/chỉnh cron trên UI: Settings > Technical > Scheduled Actions

---

## 20. Recordset Arithmetic — Phép toán tập hợp

Recordset hoạt động như Python set nhưng **giữ thứ tự** và **không trùng lặp**.

```python
a = self.search([('tag', '=', 'a')])
b = self.search([('tag', '=', 'b')])
all_recs = self.search([])

a | b        # union — gộp, loại trùng
all_recs & a # intersection — chỉ lấy record có trong cả hai
all_recs - a # difference — lấy record KHÔNG có trong a

rec in a     # True/False — kiểm tra record có trong recordset
a <= all_recs  # True nếu a là tập con của all_recs
a == b         # so sánh theo ids
```

Gom dần vào recordset (accumulator pattern):
```python
result = self.env['my.model']   # empty recordset
for rec in all_recs:
    if rec.score > 50:
        result |= rec           # thêm vào tập kết quả
```

Một vài trick hay:
```python
rec.ids          # [1, 2, 3] — không query DB thêm
rec.ensure_one() # raise UserError nếu len != 1

# mapped trả về recordset nếu field là quan hệ
children = parents.mapped('child_ids')  # => recordset, không phải list
```

---

## 21. Controller — HTTP Routes

```python
from odoo import http
from odoo.http import request

class MyController(http.Controller):

    @http.route('/my/url', type='http', auth='user', methods=['GET'])
    def my_page(self, **kwargs):
        return "<h1>Hello</h1>"
```

**`auth=`**
| Giá trị | Ý nghĩa |
|---------|---------|
| `'user'` | Phải đăng nhập (default) |
| `'public'` | Ai cũng gọi được |
| `'none'` | Tự quản lý hoàn toàn |

**`type=`**
| Giá trị | Dùng khi |
|---------|---------|
| `'http'` | Trả về HTML, redirect, file |
| `'json'` | JSON API — tự parse body, tự wrap `{result: ...}` |

```python
# JSON route — client POST body: {"department": "it"}
@http.route('/api/employees', type='json', auth='user', methods=['POST'])
def get_employees(self, department=None, **kwargs):
    recs = request.env['demo.employee'].search([('department', '=', department)])
    return recs.read(['name', 'salary'])  # tự trả về {"result": [...]}

# Trả JSON thủ công từ type='http'
return request.make_response(
    json.dumps({'count': 10}),
    headers=[('Content-Type', 'application/json')],
)
```

> `request.env` là ORM env của user đang đăng nhập — dùng như `self.env` trong model.
