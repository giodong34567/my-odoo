# 📘 Odoo Model – Tổng hợp kiến thức quan trọng

## 🔹 1. Thông tin cơ bản của model

### `_name`
- Tên model (bắt buộc khi tạo model mới)
- Format: `module.model_name`
```python
_name = 'student.profile'
```

### `_description`
- Mô tả model (hiển thị cho người dùng)
```python
_description = 'Student Profile'
```

### `_rec_name`
- Field dùng làm tên hiển thị của record
- Mặc định: `name`
```python
_rec_name = 'code'
```

### `_order`
- Sắp xếp mặc định khi search
```python
_order = 'create_date desc'
```

---

## 🔹 2. Loại model

### 🟢 Model (models.Model)
- Model bình thường (có lưu DB)
```python
class Student(models.Model):
    _name = 'student.profile'
```
- `_auto = True` (mặc định) → Có bảng DB

---

### 🟡 AbstractModel (models.AbstractModel)
- Model dùng để kế thừa (không tạo bảng)
```python
class BaseReport(models.AbstractModel):
    _name = 'base.report'
```
- `_abstract = True`
- `_auto = False`

👉 Dùng khi:
- Viết logic chung
- Không cần lưu DB

---

### 🔴 TransientModel (models.TransientModel)
- Model tạm (wizard, popup)
```python
class StudentWizard(models.TransientModel):
    _name = 'student.wizard'
```
- `_transient = True`
- Dữ liệu tự động bị xóa

👉 Dùng khi:
- Wizard
- Form tạm
- Import/export

---

## 🔹 3. Inheritance (Kế thừa)

### 🟢 `_inherit` – Kế thừa Python

#### ✔️ Extend model có sẵn
```python
_inherit = 'res.partner'
```
👉 Không tạo model mới → chỉ thêm field

#### ✔️ Tạo model mới + kế thừa
```python
_name = 'student.profile'
_inherit = ['mail.thread']
```
👉 Vừa tạo model mới, vừa dùng tính năng model khác

---

### 🔴 `_inherits` – Delegation inheritance
```python
_inherits = {
    'res.partner': 'partner_id'
}
```
👉 Ý nghĩa:
- Dùng field của model khác
- Nhưng dữ liệu vẫn lưu ở bảng gốc

---

### ⚠️ Lưu ý
Nếu nhiều model cha có field trùng tên:
```python
_inherits = {
    'a.model': 'a_id',
    'b.model': 'b_id'
}
```
👉 Field sẽ lấy theo model khai báo **sau cùng**

---

## 🔹 4. Database behavior

### `_auto`
- Có tạo bảng DB không
```python
_auto = False
```
👉 Dùng khi:
- SQL view
- Tự tạo bảng bằng `init()`

### `_abstract`
```python
_abstract = True
```
👉 Model dùng để kế thừa

### `_transient`
```python
_transient = True
```
👉 Model tạm

---

## 🔹 5. Company check

### `_check_company_auto`
```python
_check_company_auto = True
```
👉 Khi create/write:
- Odoo sẽ check company consistency

---

## 🔹 6. Tree structure (cây phân cấp)

### `_parent_name`
```python
_parent_name = 'parent_id'
```

### `_parent_store`
```python
_parent_store = True
```
👉 Khi bật:
- Tạo field `parent_path`
- Query nhanh hơn với:
  - `child_of`
  - `parent_of`

---

## 🔹 7. Kanban

### `_fold_name`
```python
_fold_name = 'fold'
```
👉 Dùng để:
- Gập/mở column trong kanban

---

## 🔹 8. TransientModel – cơ chế xóa dữ liệu

### ⏱ `_transient_max_hours`
```python
_transient_max_hours = 1.0
```
👉 Sau 1 giờ → record bị xóa

### 🔢 `_transient_max_count`
```python
_transient_max_count = 100
```
👉 Giới hạn số record

### 🧹 `_transient_vacuum()`
- Hàm tự động dọn dữ liệu
- Chạy mỗi ~5 phút

---

## 🔥 Ví dụ tổng hợp

### Model thường
```python
class Student(models.Model):
    _name = 'student.profile'
    _description = 'Student'
    _order = 'id desc'

    name = fields.Char()
```

### TransientModel
```python
class StudentWizard(models.TransientModel):
    _name = 'student.wizard'

    name = fields.Char()
```

### Extend model
```python
class StudentExtend(models.Model):
    _inherit = 'res.partner'

    student_code = fields.Char()
```

---

## 🚀 Tóm tắt nhanh

| Thuộc tính | Ý nghĩa |
|----------|--------|
| `_name` | Tên model |
| `_inherit` | Kế thừa logic |
| `_inherits` | Kế thừa dữ liệu |
| `_auto` | Tạo bảng DB |
| `_abstract` | Model base |
| `_transient` | Model tạm |
| `_rec_name` | Tên hiển thị |
| `_order` | Sắp xếp |
| `_parent_store` | Tối ưu cây |

---

## 🧠 Ghi nhớ nhanh

- `_inherit` → thêm chức năng  
- `_inherits` → dùng dữ liệu model khác  
- `Model` → lưu DB  
- `AbstractModel` → không lưu DB  
- `TransientModel` → dữ liệu tạm, auto xóa  