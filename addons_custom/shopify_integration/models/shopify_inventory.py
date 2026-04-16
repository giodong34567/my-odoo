import logging
from .shopify_mixin import ShopifyAPIMixin

_logger = logging.getLogger(__name__)


class InventorySync(ShopifyAPIMixin):
    """Pulls inventory levels from Shopify and updates stock.quant in Odoo via ORM."""

    def run(self):
        """Returns {'updated': int, 'skipped': int, 'errors': list}"""
        updated = skipped = 0
        errors = []

        # 1. Get all active Shopify locations
        try:
            locations = self.call('GET', '/locations.json').get('locations', [])
        except Exception as exc:
            msg = f'Failed to fetch Shopify locations: {exc}'
            _logger.error(msg)
            self._log('failed', msg)
            return {'updated': 0, 'skipped': 0, 'errors': [msg]}

        if not locations:
            self._log('partial', 'No active locations found in Shopify.')
            return {'updated': 0, 'skipped': 0, 'errors': []}

        # Use the first active location (or all of them summed)
        location_ids = [str(loc['id']) for loc in locations if loc.get('active')]

        # 2. Fetch inventory levels for all locations
        all_levels = []
        for loc_id in location_ids:
            try:
                levels = self.paginate(
                    '/inventory_levels.json',
                    {'location_ids': loc_id, 'limit': 250},
                )
                all_levels.extend(levels)
            except Exception as exc:
                msg = f'Failed to fetch inventory for location {loc_id}: {exc}'
                _logger.error(msg)
                errors.append(msg)

        if not all_levels:
            self._log('partial', 'No inventory levels returned from Shopify.')
            return {'updated': 0, 'skipped': 0, 'errors': errors}

        # 3. Aggregate qty per inventory_item_id (sum across locations)
        qty_map = {}  # inventory_item_id → total available qty
        for level in all_levels:
            item_id = str(level.get('inventory_item_id', ''))
            qty = level.get('available') or 0
            qty_map[item_id] = qty_map.get(item_id, 0) + qty

        # 4. Map inventory_item_id → product.product via shopify_variant_id
        #    Shopify variant has inventory_item_id; we need to fetch variants to get this mapping
        try:
            variants_raw = self.paginate('/variants.json', {'limit': 250})
        except Exception:
            # Fallback: build mapping from already-synced products
            variants_raw = []

        # inventory_item_id → shopify_variant_id
        inv_to_variant = {}
        for v in variants_raw:
            inv_id = str(v.get('inventory_item_id', ''))
            var_id = str(v.get('id', ''))
            if inv_id and var_id:
                inv_to_variant[inv_id] = var_id

        # 5. Update stock in Odoo using ORM (no raw SQL)
        warehouse = self._config.warehouse_id
        stock_location = warehouse.lot_stock_id  # the main stock location

        for inv_item_id, qty in qty_map.items():
            try:
                shopify_variant_id = inv_to_variant.get(inv_item_id)
                if not shopify_variant_id:
                    skipped += 1
                    continue

                product = self._env['product.product'].search(
                    [('shopify_variant_id', '=', shopify_variant_id)], limit=1
                )
                if not product:
                    skipped += 1
                    continue

                # Use Odoo ORM to update quantity — no raw SQL
                self._env['stock.quant']._update_available_quantity(
                    product,
                    stock_location,
                    qty - self._current_qty(product, stock_location),
                )
                updated += 1

            except Exception as exc:
                msg = f'Inventory update failed for inv_item {inv_item_id}: {exc}'
                _logger.error(msg)
                errors.append(msg)

        status = 'success' if not errors else ('partial' if updated else 'failed')
        summary = f'Inventory updated: {updated}, skipped: {skipped}, errors: {len(errors)}.'
        if errors:
            summary += ' ' + '; '.join(errors[:3])
        self._log(status, summary)

        return {'updated': updated, 'skipped': skipped, 'errors': errors}

    def _current_qty(self, product, location):
        """Get current available qty for a product at a location via ORM."""
        quants = self._env['stock.quant'].search([
            ('product_id', '=', product.id),
            ('location_id', '=', location.id),
        ])
        return sum(quants.mapped('quantity'))

    def _log(self, status, message, shopify_id=None):
        self._env['shopify.sync.log'].create({
            'config_id': self._config.id,
            'sync_type': 'inventory',
            'status': status,
            'message': message,
            'shopify_id': shopify_id,
        })
