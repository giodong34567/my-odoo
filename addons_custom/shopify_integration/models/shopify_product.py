import base64
import logging
import requests
from odoo import models, fields
from .shopify_mixin import ShopifyAPIMixin

_logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Odoo model extensions
# ---------------------------------------------------------------------------

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    shopify_id = fields.Char(string='Shopify Product ID', index=True, copy=False)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    shopify_variant_id = fields.Char(string='Shopify Variant ID', index=True, copy=False)


# ---------------------------------------------------------------------------
# ProductSync service
# ---------------------------------------------------------------------------

class ProductSync(ShopifyAPIMixin):
    """Pulls all active Shopify products/variants into Odoo."""

    def run(self):
        """Returns {'created': int, 'updated': int, 'errors': list}"""
        created = updated = 0
        errors = []

        try:
            products = self.paginate('/products.json', {'status': 'active'})
        except Exception as exc:
            msg = f'Failed to fetch products: {exc}'
            _logger.error(msg)
            self._log('failed', msg)
            return {'created': 0, 'updated': 0, 'errors': [msg]}

        for product in products:
            try:
                c, u = self._upsert_product(product)
                created += c
                updated += u
            except Exception as exc:
                msg = f'Product {product.get("id")}: {exc}'
                _logger.error(msg)
                errors.append(msg)

        status = 'success' if not errors else ('partial' if created + updated else 'failed')
        summary = f'Created: {created}, Updated: {updated}, Errors: {len(errors)}.'
        if errors:
            summary += ' ' + '; '.join(errors[:3])
        self._log(status, summary)
        return {'created': created, 'updated': updated, 'errors': errors}

    # ------------------------------------------------------------------

    def _upsert_product(self, data):
        shopify_id = str(data['id'])
        categ = self._get_or_create_category(data.get('product_type') or 'Uncategorized')

        vals = {
            'name': data.get('title', ''),
            'description_sale': data.get('body_html', ''),
            'categ_id': categ.id,
            'shopify_id': shopify_id,
        }

        # Lấy ảnh chính từ images[0] hoặc image
        image_b64 = self._fetch_image(data)
        if image_b64:
            vals['image_1920'] = image_b64

        tmpl = self._env['product.template'].search([('shopify_id', '=', shopify_id)], limit=1)
        if tmpl:
            tmpl.write(vals)
            created, updated = 0, 1
        else:
            tmpl = self._env['product.template'].create(vals)
            created, updated = 1, 0

        for variant in data.get('variants', []):
            self._upsert_variant(variant, tmpl)

        return created, updated

    def _fetch_image(self, data):
        """Download ảnh chính của sản phẩm từ Shopify, trả về base64 hoặc None."""
        # Shopify trả về 'image' (object) hoặc 'images' (list)
        image_obj = data.get('image') or {}
        src = image_obj.get('src')

        if not src:
            images = data.get('images') or []
            if images:
                src = images[0].get('src')

        if not src:
            return None

        try:
            resp = requests.get(src, timeout=15)
            if resp.ok:
                return base64.b64encode(resp.content).decode('utf-8')
        except Exception as exc:
            _logger.warning('Could not download product image %s: %s', src, exc)

        return None

    def _upsert_variant(self, data, tmpl):
        shopify_variant_id = str(data['id'])
        vals = {
            'shopify_variant_id': shopify_variant_id,
            'default_code': data.get('sku') or '',
            'lst_price': float(data.get('price') or 0.0),
            'barcode': data.get('barcode') or False,
        }

        # First try to find by shopify_variant_id
        variant = self._env['product.product'].search(
            [('shopify_variant_id', '=', shopify_variant_id)], limit=1
        )
        if variant:
            variant.write(vals)
            return

        # If template has no attributes, it already has exactly one default variant.
        # Creating another would violate the unique combination constraint.
        if not tmpl.attribute_line_ids:
            default_variant = tmpl.product_variant_ids[:1]
            if default_variant:
                default_variant.write(vals)
                return

        vals['product_tmpl_id'] = tmpl.id
        self._env['product.product'].create(vals)

    def _get_or_create_category(self, name):
        categ = self._env['product.category'].search([('name', '=', name)], limit=1)
        if not categ:
            categ = self._env['product.category'].create({'name': name})
        return categ

    def _log(self, status, message, shopify_id=None):
        self._env['shopify.sync.log'].create({
            'config_id': self._config.id,
            'sync_type': 'product',
            'status': status,
            'message': message,
            'shopify_id': shopify_id,
        })
