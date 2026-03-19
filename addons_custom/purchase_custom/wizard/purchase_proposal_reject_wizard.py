from odoo import _, api, fields, models


class PurchaseProposalRejectWizard(models.TransientModel):
    _name = "purchase.proposal.reject.wizard"
    _description = "Wizard từ chối đề xuất mua sắm"

    proposal_id = fields.Many2one(
        "purchase.proposal",
        string="Đề xuất",
        required=True,
        readonly=True,
    )
    rejection_reason = fields.Text(
        string="Lý do từ chối",
        required=True,
        placeholder="Nhập lý do từ chối đề xuất này...",
    )

    def action_confirm_reject(self):
        """Xác nhận từ chối"""
        self.ensure_one()
        proposal = self.proposal_id
        if proposal.state != "pending":
            raise models.ValidationError(
                _("Chỉ có thể từ chối đề xuất đang ở trạng thái 'Đang duyệt'!")
            )
        proposal.write({
            "state": "rejected",
            "rejection_reason": self.rejection_reason,
        })
        proposal.message_post(
            body=_("❌ Đề xuất bị từ chối bởi %s\n\n📝 Lý do: %s")
            % (self.env.user.name, self.rejection_reason),
            subtype_xmlid="mail.mt_note",
        )
        return {"type": "ir.actions.act_window_close"}
