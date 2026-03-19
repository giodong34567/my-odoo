import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class PurchaseProposal(models.Model):
    _name = "purchase.proposal"
    _description = "Đề xuất mua sắm"
    _order = "create_date desc, name desc"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "name"

    # ─────────────────────────────────────────
    # Thông tin chung
    # ─────────────────────────────────────────
    name = fields.Char(
        string="Mã đề xuất",
        required=True,
        readonly=True,
        default=lambda self: _("New"),
        copy=False,
        tracking=True,
    )

    proposer_id = fields.Many2one(
        "hr.employee",
        string="Người đề xuất",
        required=True,
        default=lambda self: self.env.user.employee_id,
        tracking=True,
        states={"draft": [("readonly", False)]},
        readonly=True,
    )

    department_id = fields.Many2one(
        "hr.department",
        string="Phòng ban",
        required=True,
        default=lambda self: self.env.user.employee_id.department_id
        if self.env.user.employee_id
        else False,
        tracking=True,
        states={"draft": [("readonly", False)]},
        readonly=True,
    )

    date_deadline = fields.Date(
        string="Ngày cần hàng",
        required=True,
        tracking=True,
        states={"draft": [("readonly", False)]},
        readonly=True,
    )

    content = fields.Text(
        string="Nội dung đề xuất",
        states={"draft": [("readonly", False)]},
        readonly=True,
    )

    vendor_id = fields.Many2one(
        "res.partner",
        string="Nhà cung cấp",
        domain="[('supplier_rank', '>', 0)]",
        tracking=True,
        states={"draft": [("readonly", False)], "pending": [("readonly", False)]},
        readonly=True,
        help="Nhà cung cấp sẽ được dùng để tạo đơn mua hàng.",
    )

    # ─────────────────────────────────────────
    # Trạng thái
    # ─────────────────────────────────────────
    state = fields.Selection(
        [
            ("draft", "Nháp"),
            ("pending", "Đang duyệt"),
            ("approved", "Đã duyệt"),
            ("rejected", "Từ chối"),
            ("order_created", "Đã tạo đơn hàng"),
        ],
        string="Trạng thái",
        default="draft",
        tracking=True,
        copy=False,
    )

    # ─────────────────────────────────────────
    # Thông tin phê duyệt
    # ─────────────────────────────────────────
    approved_by = fields.Many2one(
        "res.users",
        string="Người phê duyệt",
        readonly=True,
        copy=False,
    )
    approved_date = fields.Datetime(
        string="Ngày phê duyệt",
        readonly=True,
        copy=False,
    )
    rejection_reason = fields.Text(
        string="Lý do từ chối",
        readonly=True,
        copy=False,
    )
    request_date = fields.Datetime(
        string="Ngày gửi duyệt",
        readonly=True,
        copy=False,
    )

    # ─────────────────────────────────────────
    # Dòng sản phẩm
    # ─────────────────────────────────────────
    line_ids = fields.One2many(
        "purchase.proposal.line",
        "proposal_id",
        string="Danh sách sản phẩm",
        states={"draft": [("readonly", False)]},
        readonly=True,
    )

    # ─────────────────────────────────────────
    # Computed
    # ─────────────────────────────────────────
    currency_id = fields.Many2one(
        "res.currency",
        string="Tiền tệ",
        default=lambda self: self.env.company.currency_id,
    )

    total_amount = fields.Monetary(
        string="Tổng tiền dự kiến",
        compute="_compute_total_amount",
        store=True,
        currency_field="currency_id",
    )

    line_count = fields.Integer(
        string="Số dòng",
        compute="_compute_line_count",
    )

    order_count = fields.Integer(
        string="Số đơn hàng",
        compute="_compute_order_count",
    )

    # Quyền của user hiện tại
    can_submit = fields.Boolean(compute="_compute_user_permissions", store=False)
    can_approve = fields.Boolean(compute="_compute_user_permissions", store=False)

    # ─────────────────────────────────────────
    # CRUD
    # ─────────────────────────────────────────
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = self._generate_sequence_name()
            # Auto-fill department từ employee
            if not vals.get("department_id") and vals.get("proposer_id"):
                employee = self.env["hr.employee"].browse(vals["proposer_id"])
                if employee.department_id:
                    vals["department_id"] = employee.department_id.id
        return super().create(vals_list)

    def _generate_sequence_name(self):
        """Tạo mã đề xuất theo format: PRQ-YYYYMM-NNNNN"""
        current_date = datetime.now()
        year_month = current_date.strftime("%Y%m")

        start_of_month = current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        start_of_next_month = start_of_month + relativedelta(months=1)

        domain = [
            ("name", "like", f"PRQ-{year_month}-%"),
            ("create_date", ">=", start_of_month.strftime("%Y-%m-%d %H:%M:%S")),
            ("create_date", "<", start_of_next_month.strftime("%Y-%m-%d %H:%M:%S")),
        ]
        last_record = self.search(domain, order="name desc", limit=1)

        if last_record:
            try:
                last_seq = int(last_record.name.split("-")[-1])
                next_seq = last_seq + 1
            except (ValueError, IndexError):
                next_seq = 1
        else:
            next_seq = 1

        return f"PRQ-{year_month}-{next_seq:05d}"

    def unlink(self):
        locked = self.filtered(lambda r: r.state != "draft")
        if locked:
            names = ", ".join(locked.mapped("name"))
            raise UserError(
                _("Chỉ có thể xóa đề xuất ở trạng thái 'Nháp'!\n\nĐề xuất không thể xóa: %s") % names
            )
        return super().unlink()

    # ─────────────────────────────────────────
    # Computed methods
    # ─────────────────────────────────────────
    @api.depends("proposer_id", "state")
    def _compute_user_permissions(self):
        for record in self:
            user = self.env.user
            is_admin = user.has_group("base.group_system")
            is_manager = user.has_group("purchase_custom.group_purchase_custom_manager")

            # Proposer: người tạo hoặc user linked với employee
            is_proposer = False
            emp = getattr(user, "employee_id", False)
            if emp and record.proposer_id:
                is_proposer = emp.id == record.proposer_id.id
            if not is_proposer and record.proposer_id:
                linked_user = record.proposer_id.user_id
                is_proposer = bool(linked_user) and linked_user.id == user.id

            record.can_submit = record.state == "draft" and (is_proposer or is_admin)
            record.can_approve = record.state == "pending" and (is_manager or is_admin)

    @api.depends("line_ids.quantity", "line_ids.price_unit")
    def _compute_total_amount(self):
        for record in self:
            record.total_amount = sum(
                line.quantity * line.price_unit for line in record.line_ids
            )

    @api.depends("line_ids")
    def _compute_line_count(self):
        for record in self:
            record.line_count = len(record.line_ids)

    def _compute_order_count(self):
        for record in self:
            orders = self.env["purchase.order"].search(
                [("origin", "ilike", record.name)]
            )
            record.order_count = len(orders)

    # ─────────────────────────────────────────
    # Onchange
    # ─────────────────────────────────────────
    @api.onchange("proposer_id")
    def _onchange_proposer_id(self):
        if self.proposer_id and self.proposer_id.department_id:
            self.department_id = self.proposer_id.department_id

    # ─────────────────────────────────────────
    # Workflow actions
    # ─────────────────────────────────────────
    def action_submit(self):
        """Gửi đề xuất để duyệt"""
        for record in self:
            if record.state != "draft":
                raise UserError(_("Chỉ có thể gửi duyệt đề xuất ở trạng thái 'Nháp'!"))
            if not record.line_ids:
                raise UserError(_("Vui lòng thêm ít nhất một sản phẩm trước khi gửi duyệt!"))
            record.write({
                "state": "pending",
                "request_date": fields.Datetime.now(),
            })
            record.message_post(
                body=_("📋 Đề xuất đã được gửi để phê duyệt bởi %s") % self.env.user.name,
                subtype_xmlid="mail.mt_note",
            )

    def action_approve(self):
        """Mở dialog nhập ghi chú phê duyệt"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Phê duyệt đề xuất"),
            "res_model": "purchase.proposal.approve.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_proposal_id": self.id},
        }

    def action_reject(self):
        """Mở dialog nhập lý do từ chối"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Từ chối đề xuất"),
            "res_model": "purchase.proposal.reject.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_proposal_id": self.id},
        }

    def action_reset_to_draft(self):
        """Đặt lại về nháp"""
        for record in self:
            if record.state not in ("pending", "rejected"):
                raise UserError(_("Chỉ có thể đặt về Nháp từ trạng thái 'Đang duyệt' hoặc 'Từ chối'!"))
            record.write({
                "state": "draft",
                "approved_by": False,
                "approved_date": False,
                "rejection_reason": False,
                "request_date": False,
            })
            record.message_post(
                body=_("🔄 Đề xuất đã được đặt lại về nháp bởi %s") % self.env.user.name,
                subtype_xmlid="mail.mt_note",
            )

    # ─────────────────────────────────────────
    # Constraints
    # ─────────────────────────────────────────
    @api.constrains("date_deadline")
    def _check_date_deadline(self):
        for record in self:
            if record.date_deadline and record.state == "draft":
                if record.date_deadline < fields.Date.today():
                    raise ValidationError(_("Ngày cần hàng không được ở trong quá khứ!"))

    # ─────────────────────────────────────────
    # Purchase Order actions
    # ─────────────────────────────────────────
    def action_create_purchase_order(self):
        """Tự động tạo đơn mua hàng từ đề xuất đã duyệt và chuyển sang điều hướng tới đơn hàng"""
        self.ensure_one()
        if self.state != "approved":
            raise UserError(_("Chỉ có thể tạo đơn hàng từ đề xuất đã được phê duyệt!"))
        if not self.line_ids:
            raise UserError(_("Không có sản phẩm nào trong đề xuất!"))
        if not self.vendor_id:
            raise UserError(_("Vui lòng chọn Nhà cung cấp trước khi tạo đơn hàng!"))

        # Build order lines
        order_lines = []
        for line in self.line_ids:
            uom_id = (
                line.uom_id.id
                if line.uom_id
                else (line.product_id.uom_po_id.id or line.product_id.uom_id.id)
            )
            order_lines.append((0, 0, {
                "product_id": line.product_id.id,
                "name": line.product_id.display_name,
                "product_qty": line.quantity,
                "price_unit": line.price_unit or 0.0,
                "product_uom": uom_id,
                "date_planned": self.date_deadline
                    and fields.Datetime.from_string(str(self.date_deadline))
                    or fields.Datetime.now(),
            }))

        # Tự động tạo PO
        purchase_order = self.env["purchase.order"].create({
            "partner_id": self.vendor_id.id,
            "origin": self.name,
            "date_order": fields.Datetime.now(),
            "date_planned": self.date_deadline
                and fields.Datetime.from_string(str(self.date_deadline))
                or fields.Datetime.now(),
            "order_line": order_lines,
            "notes": self.content or False,
        })

        # Chuyển trạng thái sang Đã tạo đơn hàng
        self.write({"state": "order_created"})

        self.message_post(
            body=_("📦 Đã tạo đơn mua hàng <a href='#' data-oe-model='purchase.order' data-oe-id='%s'>%s</a>") % (
                purchase_order.id, purchase_order.name
            ),
            subtype_xmlid="mail.mt_note",
        )

        # Redirect sang đơn hàng vừa tạo
        return {
            "type": "ir.actions.act_window",
            "name": _("Đơn mua hàng"),
            "res_model": "purchase.order",
            "view_mode": "form",
            "res_id": purchase_order.id,
            "target": "current",
        }

    def action_view_purchase_orders(self):
        """Xem danh sách đơn hàng liên quan"""
        self.ensure_one()
        orders = self.env["purchase.order"].search(
            [("origin", "ilike", self.name)]
        )
        if len(orders) == 1:
            return {
                "type": "ir.actions.act_window",
                "name": _("$Đơn hàng"),
                "res_model": "purchase.order",
                "view_mode": "form",
                "res_id": orders.id,
                "target": "current",
            }
        return {
            "type": "ir.actions.act_window",
            "name": _("Đơn mua hàng"),
            "res_model": "purchase.order",
            "view_mode": "list,form",
            "domain": [("origin", "ilike", self.name)],
            "target": "current",
        }
