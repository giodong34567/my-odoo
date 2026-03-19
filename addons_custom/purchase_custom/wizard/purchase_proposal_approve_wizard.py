from odoo import _, fields, models
from odoo.exceptions import UserError


class PurchaseProposalApproveWizard(models.TransientModel):
    _name = "purchase.proposal.approve.wizard"
    _description = "Wizard phê duyệt đề xuất mua sắm"

    proposal_id = fields.Many2one(
        "purchase.proposal",
        string="Đề xuất",
        required=True,
        readonly=True,
    )
    approve_note = fields.Text(
        string="Ghi chú phê duyệt",
        placeholder="Nhập ghi chú khi phê duyệt (không bắt buộc)...",
    )

    def action_confirm_approve(self):
        """Xác nhận phê duyệt"""
        self.ensure_one()
        proposal = self.proposal_id
        if proposal.state != "pending":
            raise UserError(
                _("Chỉ có thể phê duyệt đề xuất đang ở trạng thái 'Đang duyệt'!")
            )
        proposal.write({
            "state": "approved",
            "approved_by": self.env.user.id,
            "approved_date": fields.Datetime.now(),
            "rejection_reason": False,
        })
        body = _("✅ Đề xuất đã được phê duyệt bởi %s") % self.env.user.name
        if self.approve_note:
            body += _("\n\n📝 Ghi chú: %s") % self.approve_note
        proposal.message_post(
            body=body,
            subtype_xmlid="mail.mt_note",
        )
        return {"type": "ir.actions.act_window_close"}
