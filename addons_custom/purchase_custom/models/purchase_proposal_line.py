from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PurchaseProposalLine(models.Model):
    _name = "purchase.proposal.line"
    _description = "Dòng đề xuất mua sắm"
    _order = "proposal_id, sequence, id"

    proposal_id = fields.Many2one(
        "purchase.proposal",
        string="Đề xuất",
        required=True,
        ondelete="cascade",
    )
    sequence = fields.Integer(string="Thứ tự", default=10)

    # Thông tin sản phẩm
    product_id = fields.Many2one(
        "product.product",
        string="Sản phẩm/Dịch vụ",
        required=True,
        domain=[("purchase_ok", "=", True)],
    )
    quantity = fields.Float(string="Số lượng", required=True, default=1.0)
    uom_id = fields.Many2one(
        "uom.uom",
        string="Đơn vị tính",
    )
    price_unit = fields.Monetary(
        string="Đơn giá dự kiến",
        currency_field="currency_id",
        default=0.0,
    )
    currency_id = fields.Many2one(
        "res.currency",
        related="proposal_id.currency_id",
        store=False,
    )
    note = fields.Text(string="Ghi chú")

    # State liên kết từ proposal
    state = fields.Selection(
        related="proposal_id.state",
        store=True,
    )

    # ─────────────────────────────────────────
    # Onchange
    # ─────────────────────────────────────────
    @api.onchange("product_id")
    def _onchange_product_id(self):
        if self.product_id:
            # Tự điền đơn vị tính: ưu tiên uom mua hàng, fallback uom mặc định
            self.uom_id = (
                self.product_id.uom_po_id
                or self.product_id.uom_id
                or False
            )
            # Tự động lấy giá từ bảng giá NCC nếu có
            supplier_info = self.env["product.supplierinfo"].search(
                [
                    "|",
                    ("product_id", "=", self.product_id.id),
                    ("product_tmpl_id", "=", self.product_id.product_tmpl_id.id),
                    ("company_id", "in", [False, self.env.company.id]),
                ],
                order="sequence, price",
                limit=1,
            )
            if supplier_info:
                self.price_unit = supplier_info.price
        else:
            self.uom_id = False
            self.price_unit = 0.0

    # ─────────────────────────────────────────
    # Constraints
    # ─────────────────────────────────────────
    @api.constrains("quantity")
    def _check_quantity(self):
        for record in self:
            if record.quantity <= 0:
                raise ValidationError(_("Số lượng phải lớn hơn 0!"))
