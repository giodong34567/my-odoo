import logging
from odoo import models, fields, _

_logger = logging.getLogger(__name__)


class ShopifySyncWizard(models.TransientModel):
    _name = 'shopify.sync.wizard'
    _description = 'Shopify Manual Sync Wizard'

    config_id = fields.Many2one('shopify.config', string='Store', required=True)
    sync_type = fields.Selection([
        ('products', 'Products'),
        ('inventory', 'Inventory'),
        ('orders', 'Orders'),
        ('all', 'All'),
    ], string='Sync Type', required=True, default='products')
    date_from = fields.Datetime(string='Orders From')
    date_to = fields.Datetime(string='Orders To')
    result_summary = fields.Text(string='Result', readonly=True)

    def action_run_sync(self):
        self.ensure_one()
        parts = []
        try:
            if self.sync_type in ('products', 'all'):
                r = self.config_id._run_product_sync()
                parts.append(
                    _('Products — created: %s, updated: %s, errors: %s')
                    % (r['created'], r['updated'], len(r['errors']))
                )

            if self.sync_type in ('orders', 'all'):
                r = self.config_id._run_order_import(
                    date_from=self.date_from or None,
                    date_to=self.date_to or None,
                )
                parts.append(
                    _('Orders — created: %s, skipped: %s, errors: %s')
                    % (r['created'], r['skipped'], len(r['errors']))
                )

            if self.sync_type == 'inventory':
                parts.append(_('Inventory sync is not yet implemented.'))

        except Exception as exc:
            _logger.error('SyncWizard error: %s', exc)
            parts.append(_('Error: %s') % exc)

        self.result_summary = '\n'.join(parts) or _('Nothing was synced.')

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'shopify.sync.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
