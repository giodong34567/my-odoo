from odoo import api, fields, models


class DemoProductVariant(models.Model):
    """
    MODEL CON — lưu thông tin RIÊNG của từng biến thể.

    Bảng DB: demo_product_variant
    Chứa những thứ khác nhau giữa các biến thể:
    màu sắc, kích cỡ, giá điều chỉnh, tồn kho...

    Tương tự: product.product trong Odoo gốc.

    ┌─────────────────────────────────────────────────────┐
    │  DELEGATION INHERITANCE hoạt động thế nào?          │
    │                                                     │
    │  demo_product_template (cha)                        │
    │  ┌────┬──────────┬────────────┬──────────┐          │
    │  │ id │ name     │ base_price │ category │          │
    │  │  1 │ Áo thun  │ 100,000    │ clothing │          │
    │  └────┴──────────┴────────────┴──────────┘          │
    │           ↑            ↑            ↑               │
    │  demo_product_variant (con)                         │
    │  ┌────┬─────────────┬───────┬──────┬───────────┐    │
    │  │ id │ template_id │ color │ size │ extra_price│   │
    │  │  1 │      1      │ Đỏ    │ S    │  10,000   │    │
    │  │  2 │      1      │ Xanh  │ M    │  10,000   │    │
    │  │  3 │      1      │ Trắng │ L    │  20,000   │    │
    │  └────┴─────────────┴───────┴──────┴───────────┘    │
    │                                                     │
    │  variant.name       => đọc từ template.name         │
    │  variant.base_price => đọc từ template.base_price   │
    │  variant.color      => đọc từ bảng variant          │
    └─────────────────────────────────────────────────────┘
    """
    _name = 'demo.product.variant'
    _description = 'Biến thể sản phẩm'
    _order = 'template_id, color, size'

    # ── DELEGATION LINK ───────────────────────────────────────────
    # Khai báo _inherits trước, sau đó khai báo field link tường minh.
    # Odoo sẽ tự tạo record demo.product.template nếu không truyền template_id.
    _inherits = {'demo.product.template': 'template_id'}

    template_id = fields.Many2one(
        comodel_name='demo.product.template',
        string='Mẫu sản phẩm',
        ondelete='cascade',   # xóa template => xóa tất cả biến thể
        required=False,       # không required vì Odoo tự tạo nếu thiếu
    )

    # ── FIELD RIÊNG CỦA BIẾN THỂ ─────────────────────────────────
    # Các field này chỉ lưu trong bảng demo_product_variant
    color = fields.Selection([
        ('red',   'Đỏ'),
        ('blue',  'Xanh'),
        ('white', 'Trắng'),
        ('black', 'Đen'),
    ], string='Màu sắc')

    size = fields.Selection([
        ('s', 'S'),
        ('m', 'M'),
        ('l', 'L'),
        ('xl', 'XL'),
    ], string='Kích cỡ')

    extra_price = fields.Float(
        string='Giá thêm',
        default=0.0,
        help='Cộng thêm vào giá gốc của mẫu sản phẩm',
    )

    stock = fields.Integer(string='Tồn kho', default=0)

    # ── COMPUTE: kết hợp field từ CHA và CON ─────────────────────
    # Đây là điểm hay của delegation:
    # compute có thể dùng field từ cả 2 bảng một cách tự nhiên
    final_price = fields.Float(
        string='Giá bán',
        compute='_compute_final_price',
        store=True,
    )

    @api.depends('base_price', 'extra_price')
    def _compute_final_price(self):
        for variant in self:
            # base_price đến từ demo.product.template (qua delegation)
            # extra_price đến từ demo.product.variant (bảng này)
            variant.final_price = variant.base_price + variant.extra_price

    # ── DISPLAY NAME ──────────────────────────────────────────────
    @api.depends('name', 'color', 'size')
    def _compute_display_name(self):
        for variant in self:
            parts = [variant.name or '(Chưa đặt tên)']
            if variant.color:
                color_label = dict(self._fields['color'].selection).get(variant.color, '')
                parts.append(color_label)
            if variant.size:
                parts.append(variant.size.upper())
            variant.display_name = ' / '.join(parts)
