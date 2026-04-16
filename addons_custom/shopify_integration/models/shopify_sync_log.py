from odoo import models, fields


class ShopifySyncLog(models.Model):
    _name = 'shopify.sync.log'
    _description = 'Shopify Sync Log'
    _order = 'create_date desc, id desc'

    config_id = fields.Many2one('shopify.config', string='Store', required=True, ondelete='cascade')
    sync_type = fields.Selection([
        ('product', 'Sản phẩm'),
        ('inventory', 'Tồn kho'),
        ('order', 'Đơn hàng'),
    ], string='Loại đồng bộ', required=True)
    status = fields.Selection([
        ('success', 'Thành công'),
        ('partial', 'Một phần'),
        ('failed', 'Thất bại'),
    ], string='Trạng thái', required=True)
    message = fields.Text(string='Message')
    shopify_id = fields.Char(string='Shopify ID')
    # create_date (auto) serves as the timestamp; we expose it as a readable field
    timestamp = fields.Datetime(
        string='Timestamp', default=fields.Datetime.now, readonly=True,
    )
