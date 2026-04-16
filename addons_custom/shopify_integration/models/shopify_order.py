import logging
from datetime import datetime
from odoo import models, fields
from .shopify_mixin import ShopifyAPIMixin

_logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Odoo model extension
# ---------------------------------------------------------------------------

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    shopify_order_id = fields.Char(string='Shopify Order ID', index=True, copy=False)


# ---------------------------------------------------------------------------
# OrderImport service
# ---------------------------------------------------------------------------

class OrderImport(ShopifyAPIMixin):
    """Pulls Shopify orders and creates confirmed sale.order records in Odoo."""

    def run(self, date_from=None, date_to=None):
        """Returns {'created': int, 'skipped': int, 'errors': list}"""
        created = skipped = 0
        errors = []
        unrecoverable = False

        try:
            params = {'status': 'any'}
            lower = date_from or self._config.last_sync
            if lower:
                params['created_at_min'] = (
                    lower.strftime('%Y-%m-%dT%H:%M:%S')
                    if hasattr(lower, 'strftime') else str(lower)
                )
            if date_to:
                params['created_at_max'] = (
                    date_to.strftime('%Y-%m-%dT%H:%M:%S')
                    if hasattr(date_to, 'strftime') else str(date_to)
                )
            orders = self.paginate('/orders.json', params)
        except Exception as exc:
            msg = f'Failed to fetch orders: {exc}'
            _logger.error(msg)
            self._log('failed', msg)
            return {'created': 0, 'skipped': 0, 'errors': [msg]}

        for order in orders:
            try:
                shopify_order_id = str(order['id'])

                existing = self._env['sale.order'].search(
                    [('shopify_order_id', '=', shopify_order_id)], limit=1
                )
                if existing:
                    # Nếu đã tồn tại nhưng chưa có lines (lần trước sync lỗi),
                    # thử tạo lines lại thay vì skip hoàn toàn
                    if existing.state == 'draft' and not existing.order_line:
                        has_lines = self._create_lines(existing, order)
                        if has_lines:
                            existing.action_confirm()
                            created += 1
                        else:
                            skipped += 1
                    else:
                        skipped += 1
                    continue

                partner = self._get_or_create_partner(order)
                shipping = self._get_or_create_shipping(order, partner)

                so = self._env['sale.order'].create({
                    'shopify_order_id': shopify_order_id,
                    'partner_id': partner.id,
                    'partner_shipping_id': shipping.id,
                    'warehouse_id': self._config.warehouse_id.id,
                })

                has_lines = self._create_lines(so, order)
                if has_lines:
                    so.action_confirm()
                else:
                    # Tạo order nhưng không có lines — vẫn ghi nhận để retry sau
                    _logger.warning('Order %s created with no lines — products may not be synced yet.', shopify_order_id)

                created += 1

            except Exception as exc:
                msg = f'Order {order.get("id")}: {exc}'
                _logger.error(msg)
                errors.append(msg)
                unrecoverable = True

        if unrecoverable:
            self._log('failed', 'Unrecoverable errors: ' + '; '.join(errors[:3]))
        else:
            self._config.last_sync = datetime.now()
            status = 'success' if not errors else 'partial'
            summary = f'Created: {created}, Skipped: {skipped}, Errors: {len(errors)}.'
            if errors:
                summary += ' ' + '; '.join(errors[:3])
            self._log(status, summary)

        return {'created': created, 'skipped': skipped, 'errors': errors}

    # ------------------------------------------------------------------

    def _get_or_create_partner(self, order):
        customer = order.get('customer') or {}
        email = customer.get('email') or order.get('email', '')
        name = (
            f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip()
            or email or 'Shopify Customer'
        )
        if email:
            partner = self._env['res.partner'].search([('email', '=', email)], limit=1)
            if partner:
                return partner
        return self._env['res.partner'].create({'name': name, 'email': email})

    def _get_or_create_shipping(self, order, parent):
        addr = order.get('shipping_address') or {}
        return self._env['res.partner'].create({
            'name': addr.get('name') or parent.name,
            'parent_id': parent.id,
            'type': 'delivery',
            'street': addr.get('address1', ''),
            'street2': addr.get('address2', ''),
            'city': addr.get('city', ''),
            'zip': addr.get('zip', ''),
            'phone': addr.get('phone', ''),
        })

    def _create_lines(self, so, order):
        has_lines = False
        for line in order.get('line_items', []):
            product = self._find_product(line)
            if not product:
                sku = line.get('sku', '')
                variant_id = str(line.get('variant_id', ''))
                self._log(
                    'partial',
                    f'Order {so.shopify_order_id}: SKU "{sku}" / variant_id "{variant_id}" not found — line skipped.',
                    shopify_id=so.shopify_order_id,
                )
                continue
            self._env['sale.order.line'].create({
                'order_id': so.id,
                'product_id': product.id,
                'product_uom_qty': float(line.get('quantity', 1)),
                'price_unit': float(line.get('price', 0.0)),
                'name': line.get('title') or product.name,
            })
            has_lines = True
        return has_lines

    def _find_product(self, line):
        """Find product.product by variant_id first, then SKU, then product title."""
        env = self._env

        # 1. Match by Shopify variant ID (most reliable)
        variant_id = line.get('variant_id')
        if variant_id:
            product = env['product.product'].search(
                [('shopify_variant_id', '=', str(variant_id))], limit=1
            )
            if product:
                return product

        # 2. Match by SKU / default_code
        sku = line.get('sku', '').strip()
        if sku:
            product = env['product.product'].search(
                [('default_code', '=', sku)], limit=1
            )
            if product:
                return product

        # 3. Match by product title as last resort
        title = line.get('title', '').strip()
        if title:
            tmpl = env['product.template'].search(
                [('name', '=ilike', title)], limit=1
            )
            if tmpl and tmpl.product_variant_ids:
                return tmpl.product_variant_ids[0]

        return None

    def _log(self, status, message, shopify_id=None):
        self._env['shopify.sync.log'].create({
            'config_id': self._config.id,
            'sync_type': 'order',
            'status': status,
            'message': message,
            'shopify_id': shopify_id,
        })
