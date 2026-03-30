from odoo import fields, models


class DemoProductTemplate(models.Model):
    """
    MODEL CHA — lưu thông tin CHUNG của sản phẩm.

    Bảng DB: demo_product_template
    Chứa những thứ không thay đổi giữa các biến thể:
    tên, mô tả, giá gốc, danh mục...

    Tương tự: product.template trong Odoo gốc.
    """
    _name = 'demo.product.template'
    _description = 'Mẫu sản phẩm'
    _order = 'name'

    name        = fields.Char(string='Tên sản phẩm', required=True)
    description = fields.Text(string='Mô tả')
    base_price  = fields.Float(string='Giá gốc', required=True, default=0.0)
    category    = fields.Selection([
        ('clothing', 'Quần áo'),
        ('shoes',    'Giày dép'),
        ('bag',      'Túi xách'),
    ], string='Danh mục', required=True)
    active      = fields.Boolean(default=True)
