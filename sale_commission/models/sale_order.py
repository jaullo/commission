# Copyright 2014-2020 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.depends("order_line.agents.amount")
    def _compute_commission_total(self):
        for record in self:
            record.commission_total = sum(record.mapped("order_line.agents.amount"))

    commission_total = fields.Float(
        string="Commissions", compute="_compute_commission_total", store=True,
    )

    def recompute_lines_agents(self):
        self.mapped("order_line").recompute_agents()


class SaleOrderLine(models.Model):
    _inherit = [
        "sale.order.line",
        "sale.commission.mixin",
    ]
    _name = "sale.order.line"

    agents = fields.One2many(
        string="Agents & commissions", comodel_name="sale.order.line.agent",
    )

    @api.depends("order_id.partner_id")
    def _compute_agent_ids(self):
        for record in self:
            record.agents = record._prepare_agents_vals_partner(
                record.order_id.partner_id
            )

    def _prepare_invoice_line(self):
        vals = super(SaleOrderLine, self)._prepare_invoice_line()
        vals["agents"] = [
            (0, 0, {"agent": x.agent.id, "commission": x.commission.id})
            for x in self.agents
        ]
        return vals


class SaleOrderLineAgent(models.Model):
    _inherit = "sale.commission.line.mixin"
    _name = "sale.order.line.agent"

    object_id = fields.Many2one(comodel_name="sale.order.line", oldname="sale_line",)
    currency_id = fields.Many2one(related="object_id.currency_id", readonly=True,)

    @api.depends("object_id.price_subtotal")
    def _compute_amount(self):
        for line in self:
            order_line = line.object_id
            line.amount = line._get_commission_amount(
                line.commission,
                order_line.price_subtotal,
                order_line.product_id,
                order_line.product_uom_qty,
            )
