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
