import logging
from odoo import models, fields, _
from odoo.exceptions import UserError
from .shopify_mixin import ShopifyAPIMixin

_logger = logging.getLogger(__name__)


class ShopifyConfig(models.Model):
    _name = 'shopify.config'
    _description = 'Shopify Store Configuration'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Store Name', required=True, tracking=True)
    shop_url = fields.Char(
        string='Shop URL', required=True, tracking=True,
        help='e.g. https://my-store.myshopify.com',
    )
    access_token = fields.Char(
        string='Access Token', required=True,
        help='Shopify Admin API access token — stored securely, never shown in logs.',
    )
    warehouse_id = fields.Many2one(
        'stock.warehouse', string='Warehouse', required=True,
        help='Odoo warehouse that maps to this Shopify store.',
    )
    last_sync = fields.Datetime(string='Last Successful Sync', readonly=True, tracking=True)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('shop_url_unique', 'UNIQUE(shop_url)', 'A configuration for this shop URL already exists.'),
    ]

    def action_test_connection(self):
        self.ensure_one()
        try:
            _ShopifyTest(self).call('GET', '/shop.json')
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Connection Successful'),
                    'message': _('Connected to "%s" successfully.') % self.name,
                    'type': 'success',
                    'sticky': False,
                },
            }
        except UserError as exc:
            raise UserError(_('Connection failed: %s') % exc) from exc
        except Exception as exc:
            raise UserError(_('Connection failed: %s') % exc) from exc

    def action_sync_products(self):
        """Entry point for the product sync cron — no import statements needed in XML."""
        for config in self.search([('active', '=', True)]):
            try:
                config._run_product_sync()
            except Exception as exc:
                _logger.error('Product sync failed for %s: %s', config.name, exc)
                self.env['shopify.sync.log'].create({
                    'config_id': config.id,
                    'sync_type': 'product',
                    'status': 'failed',
                    'message': str(exc),
                })

    def action_sync_orders(self):
        """Entry point for the order import cron — no import statements needed in XML."""
        for config in self.search([('active', '=', True)]):
            try:
                config._run_order_import()
            except Exception as exc:
                _logger.error('Order import failed for %s: %s', config.name, exc)
                self.env['shopify.sync.log'].create({
                    'config_id': config.id,
                    'sync_type': 'order',
                    'status': 'failed',
                    'message': str(exc),
                })

    def _run_product_sync(self):
        from .shopify_product import ProductSync
        return ProductSync(self).run()

    def _run_order_import(self, date_from=None, date_to=None):
        from .shopify_order import OrderImport
        return OrderImport(self).run(date_from=date_from, date_to=date_to)


class _ShopifyTest(ShopifyAPIMixin):
    """Minimal wrapper used only for the connection test."""
